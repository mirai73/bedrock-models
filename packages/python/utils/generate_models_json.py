#!/usr/bin/env python3
"""
Script to scan all AWS regions and retrieve foundation model IDs available in each region.
Maps each unique model ID to the list of regions where it's supported and the inference types.
Uses ThreadPoolExecutor for parallel processing to speed up scanning.
"""

import boto3
import json
import logging
import http.client
import socket
import ssl
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set, Any
import threading
import urllib.request
import urllib.error
from botocore.config import Config
from botocore.exceptions import ReadTimeoutError, ConnectTimeoutError, ClientError
from aws_bedrock_token_generator import provide_token


logger = logging.getLogger(__name__)

# Disable boto3's built-in retries so retry_on_timeout is the single, uniform
# retry layer (exponential backoff) across every API call.
BEDROCK_CLIENT_CONFIG = Config(retries={'max_attempts': 1})

# Exception types that represent a timeout or connection drop worth retrying.
_RETRYABLE_EXCEPTIONS = (
    socket.timeout,
    TimeoutError,
    ReadTimeoutError,
    ConnectTimeoutError,
    ConnectionError,  # Covers ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError, BrokenPipeError
    http.client.RemoteDisconnected,
    http.client.IncompleteRead,
    http.client.ResponseNotReady,
    http.client.HTTPException,
    ssl.SSLError,
)


def _is_retryable(exc: Exception) -> bool:
    """Return True if the exception represents a retryable timeout, dropped connection, throttling error, or server error."""
    if isinstance(exc, _RETRYABLE_EXCEPTIONS):
        return True
    if isinstance(exc, ClientError):
        error_code = exc.response.get('Error', {}).get('Code', '')
        if error_code in ('ThrottlingException', 'RequestLimitExceeded', 'ProvisionedThroughputExceededException'):
            return True
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code in (429, 500, 502, 503, 504):
            return True
        return False
    # urllib wraps socket errors, timeouts, and connection drops inside URLError.
    if isinstance(exc, urllib.error.URLError):
        reason = getattr(exc, 'reason', None)
        if isinstance(reason, _RETRYABLE_EXCEPTIONS):
            return True
        if isinstance(reason, (OSError, socket.error)):
            return True
        if isinstance(reason, str) and any(kw in reason.lower() for kw in ('timeout', 'timed out', 'connection reset', 'closed connection', 'remote disconnected', 'broken pipe')):
            return True
    if isinstance(exc, (OSError, socket.error)):
        return True
    return False


def make_bedrock_client(region: str):
    """Create a Bedrock client with internal retries disabled."""
    return boto3.client('bedrock', region_name=region, config=BEDROCK_CLIENT_CONFIG)


def retry_on_timeout(func, *args, max_retries: int = 3, base_delay: float = 1.0,
                     description: str = '', **kwargs):
    """
    Call ``func(*args, **kwargs)``, retrying on timeout or throttling up to ``max_retries``
    times with exponential backoff (``base_delay * 2**attempt``).

    Only timeout and throttling errors are retried; all other exceptions propagate immediately.
    Every retryable error is logged: each retry as a warning and the final, exhausted attempt as an error.
    """
    label = description or getattr(func, '__name__', 'API call')
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            if not _is_retryable(exc):
                raise
            last_exc = exc
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    "Retryable error on %s (attempt %d/%d): %s; retrying in %.1fs",
                    label, attempt + 1, max_retries + 1, exc, delay,
                )
                time.sleep(delay)
            else:
                logger.error(
                    "Error on %s after %d attempts, giving up: %s",
                    label, max_retries + 1, exc,
                )
    raise last_exc


def get_bedrock_regions() -> List[str]:
    """Get regions where Bedrock service is available."""
    session = boto3.Session()
    return session.get_available_regions('bedrock')


def get_foundation_models_in_region(region: str) -> tuple[str, List[Dict] | None]:
    """
    Get all foundation models available in a specific region.
    
    Args:
        region: AWS region name
        
    Returns:
        Tuple of (region, list of model dictionaries or None on failure)
    """
    try:
        bedrock = make_bedrock_client(region)
        response = retry_on_timeout(
            bedrock.list_foundation_models,
            description=f"list_foundation_models in {region}",
        )
        return region, response.get('modelSummaries', [])
    except Exception as e:
        print(f"Error accessing region {region}: {e}")
        return region, None


def get_inference_profiles_in_region(region: str) -> Dict[str, Dict[str, List[str]]] | None:
    """
    Get all inference profiles available in a specific region and their covered regions.
    Maps model IDs to a dictionary of profile prefixes and their covered regions.
    
    Args:
        region: AWS region name
        
    Returns:
        Dictionary mapping model IDs to profile info or None on failure
    """
    try:
        bedrock = make_bedrock_client(region)
        response = retry_on_timeout(
            bedrock.list_inference_profiles,
            description=f"list_inference_profiles in {region}",
        )
        
        # Structure: model_id -> {prefix -> [regions]}
        model_profiles = defaultdict(lambda: defaultdict(list))
        
        for profile in response.get('inferenceProfileSummaries', []):
            profile_id = profile.get('inferenceProfileId', '')
            
            # Extract prefix from profile ID (e.g., "us.anthropic...:0" -> "US")
            if '.' in profile_id:
                parts = profile_id.split('.')
                prefix = parts[0].upper()
                model_id = '.'.join(parts[1:])
                
                # Fetch detailed profile info to get covered regions
                try:
                    details = retry_on_timeout(
                        bedrock.get_inference_profile,
                        inferenceProfileIdentifier=profile_id,
                        description=f"get_inference_profile {profile_id} in {region}",
                    )
                    covered_regions = set()
                    
                    for model in details.get('models', []):
                        # Arn format: arn:aws:bedrock:REGION::...
                        arn = model.get('modelArn', '')
                        if ':' in arn:
                            arn_parts = arn.split(':')
                            if len(arn_parts) > 3:
                                region_part = arn_parts[3]
                                if region_part:
                                    covered_regions.add(region_part)
                    
                    if covered_regions:
                        model_profiles[model_id][prefix] = sorted(list(covered_regions))
                        
                except Exception as e:
                    # If we can't get details, just record the prefix exists (backward compatibility)
                    print(f"    ⚠ Could not get details for profile {profile_id}: {e}")
                    if prefix not in model_profiles[model_id]:
                        model_profiles[model_id][prefix] = []

        # Convert to standard dict for return
        return {k: dict(v) for k, v in model_profiles.items()}
    except Exception as e:
        print(f"  Error listing inference profiles in {region}: {e}")
        return None


def get_mantle_models_in_region(region: str) -> tuple[Dict[str, List[str]] | None, set[str]]:
    """
    Query all models on the Bedrock Mantle endpoint in a specific region,
    and probe their support for completions and responses endpoints using validation-only check.
    
    Returns:
        Tuple of (model_apis dictionary or None on failure, set of failed_model_ids)
    """
    try:
        token = provide_token(region=region)
    except Exception as e:
        print(f"  ⚠ Could not generate Mantle token for {region}: {e}")
        return {}, set()
        
    url_models = f"https://bedrock-mantle.{region}.api.aws/v1/models"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url_models, headers=headers)
    try:
        with retry_on_timeout(
            urllib.request.urlopen, req, timeout=10,
            description=f"Mantle list models in {region}",
        ) as response:
            data = json.loads(response.read().decode())
            model_ids = [m['id'] for m in data.get('data', [])]
    except Exception as exc:
        if _is_retryable(exc):
            print(f"  ⚠ Mantle endpoint error/timeout in {region}: {exc}")
            return None, set()
        # If the endpoint doesn't exist or isn't reachable (e.g. host name unresolved), return empty dict
        return {}, set()
        
    def probe_model(model_id):
        supported_apis = []
        probe_failed = False
        
        # 1. Probe completions API
        if not model_id.startswith('anthropic.'):
            comp_success = False
            url_comp = f"https://bedrock-mantle.{region}.api.aws/v1/chat/completions"
            payload_comp = {
                "model": model_id,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": -1
            }
            req_comp = urllib.request.Request(url_comp, data=json.dumps(payload_comp).encode(), headers=headers, method='POST')
            try:
                with retry_on_timeout(
                    urllib.request.urlopen, req_comp, timeout=5,
                    description=f"Mantle completions probe {model_id} in {region}",
                ) as r:
                    pass
            except urllib.error.HTTPError as e:
                body = e.read().decode()
                if 'max_tokens' in body or 'access_denied' in body:
                    supported_apis.append('completions')
                    comp_success = True
                else:
                    logger.warning("Mantle completions probe for %s in %s returned unexpected HTTP %d: %s", model_id, region, e.code, body[:200])
                    probe_failed = True
            except Exception as e:
                logger.warning("Mantle completions probe failed for %s in %s: %s", model_id, region, e)
                probe_failed = True
                
            # Fallback to /openai/v1/chat/completions
            if not comp_success:
                url_comp_openai = f"https://bedrock-mantle.{region}.api.aws/openai/v1/chat/completions"
                req_comp_openai = urllib.request.Request(url_comp_openai, data=json.dumps(payload_comp).encode(), headers=headers, method='POST')
                try:
                    with retry_on_timeout(
                        urllib.request.urlopen, req_comp_openai, timeout=5,
                        description=f"Mantle completions(openai) probe {model_id} in {region}",
                    ) as r:
                        pass
                except urllib.error.HTTPError as e:
                    body = e.read().decode()
                    if 'max_tokens' in body or 'access_denied' in body:
                        supported_apis.append('completions')
                    else:
                        logger.warning("Mantle completions(openai) probe for %s in %s returned unexpected HTTP %d: %s", model_id, region, e.code, body[:200])
                except Exception as e:
                    logger.warning("Mantle completions(openai) probe failed for %s in %s: %s", model_id, region, e)
            
        # 2. Probe responses API
        if not model_id.startswith('anthropic.'):
            resp_success = False
            url_resp = f"https://bedrock-mantle.{region}.api.aws/v1/responses"
            payload_resp = {
                "model": model_id,
                "input": "hi",
                "max_output_tokens": -1,
                "store": False
            }
            req_resp = urllib.request.Request(url_resp, data=json.dumps(payload_resp).encode(), headers=headers, method='POST')
            try:
                with retry_on_timeout(
                    urllib.request.urlopen, req_resp, timeout=5,
                    description=f"Mantle responses probe {model_id} in {region}",
                ) as r:
                    pass
            except urllib.error.HTTPError as e:
                body = e.read().decode()
                if 'max_output_tokens' in body or 'access_denied' in body:
                    supported_apis.append('responses')
                    resp_success = True
                else:
                    logger.warning("Mantle responses probe for %s in %s returned unexpected HTTP %d: %s", model_id, region, e.code, body[:200])
                    probe_failed = True
            except Exception as e:
                logger.warning("Mantle responses probe failed for %s in %s: %s", model_id, region, e)
                probe_failed = True
                
            # Fallback to /openai/v1/responses
            if not resp_success:
                url_resp_openai = f"https://bedrock-mantle.{region}.api.aws/openai/v1/responses"
                req_resp_openai = urllib.request.Request(url_resp_openai, data=json.dumps(payload_resp).encode(), headers=headers, method='POST')
                try:
                    with retry_on_timeout(
                        urllib.request.urlopen, req_resp_openai, timeout=5,
                        description=f"Mantle responses(openai) probe {model_id} in {region}",
                    ) as r:
                        pass
                except urllib.error.HTTPError as e:
                    body = e.read().decode()
                    if 'max_output_tokens' in body or 'access_denied' in body:
                        supported_apis.append('responses')
                    else:
                        logger.warning("Mantle responses(openai) probe for %s in %s returned unexpected HTTP %d: %s", model_id, region, e.code, body[:200])
                except Exception as e:
                    logger.warning("Mantle responses(openai) probe failed for %s in %s: %s", model_id, region, e)
            
        # 3. Probe messages API
        if model_id.startswith('anthropic.'):
            url_msg = f"https://bedrock-mantle.{region}.api.aws/anthropic/v1/messages"
            payload_msg = {
                "model": model_id,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": -1
            }
            req_msg = urllib.request.Request(url_msg, data=json.dumps(payload_msg).encode(), headers=headers, method='POST')
            try:
                with retry_on_timeout(
                    urllib.request.urlopen, req_msg, timeout=5,
                    description=f"Mantle messages probe {model_id} in {region}",
                ) as r:
                    pass
            except urllib.error.HTTPError as e:
                body = e.read().decode()
                if 'max_tokens' in body or 'access_denied' in body:
                    supported_apis.append('messages')
                else:
                    logger.warning("Mantle messages probe for %s in %s returned unexpected HTTP %d: %s", model_id, region, e.code, body[:200])
                    probe_failed = True
            except Exception as e:
                logger.warning("Mantle messages probe failed for %s in %s: %s", model_id, region, e)
                probe_failed = True
            
        return model_id, sorted(supported_apis) if supported_apis else None, probe_failed

    model_apis = {}
    failed_model_ids = set()
    with ThreadPoolExecutor(max_workers=10) as inner_executor:
        futures = [inner_executor.submit(probe_model, m) for m in model_ids]
        for f in as_completed(futures):
            res = f.result()
            if res:
                m_id, apis, failed = res
                if apis:
                    model_apis[m_id] = apis
                if failed:
                    failed_model_ids.add(m_id)
                
    return model_apis, failed_model_ids


def process_region(region: str) -> tuple[str, List[Dict], Dict[str, Dict[str, List[str]]], int, Dict[str, List[str]], bool, set[str]]:
    """
    Process a single region: get models, inference profiles, and Mantle models.
    
    Args:
        region: AWS region name
        
    Returns:
        Tuple of (region, filtered_models, model_to_profiles, excluded_count, mantle_model_apis, failed, failed_probe_models)
    """
    print(f"Scanning region: {region}")
    failed = False
    
    region_name, models = get_foundation_models_in_region(region)
    if models is None:
        print(f"  ⚠ Failed to fetch foundation models in {region}")
        models = []
        failed = True
    else:
        print(f"  Found {len(models)} models in {region}")
    
    # Filter models immediately - only keep those with ON_DEMAND or INFERENCE_PROFILE
    filtered_models = []
    excluded_count = 0
    
    for model in models:
        inference_types = model.get('inferenceTypesSupported', [])
        if 'ON_DEMAND' in inference_types or 'INFERENCE_PROFILE' in inference_types:
            filtered_models.append(model)
        else:
            excluded_count += 1
            model_id = model.get('modelId', 'unknown')
#            print(f"    ⓧ Excluding {model_id} (only PROVISIONED)")
    
    print(f"  Kept {len(filtered_models)} models after filtering")
    
    # Get all inference profiles in this region
    model_to_profiles = get_inference_profiles_in_region(region)
    if model_to_profiles is None:
        print(f"  ⚠ Failed to fetch inference profiles in {region}")
        model_to_profiles = {}
        failed = True
    elif model_to_profiles:
        count = sum(len(profiles) for profiles in model_to_profiles.values())
        print(f"  Found {count} profile definitions")
        
    # Get all Bedrock Mantle models and their supported APIs
    print(f"  Probing Bedrock Mantle models in {region}...")
    mantle_model_apis, failed_probe_models = get_mantle_models_in_region(region)
    if mantle_model_apis is None:
        print(f"  ⚠ Failed to probe Mantle models in {region}")
        mantle_model_apis = {}
        failed_probe_models = set()
        failed = True
    else:
        print(f"  Found {len(mantle_model_apis)} Mantle-supported models in {region}")
        if failed_probe_models:
            print(f"  ⚠ {len(failed_probe_models)} model probe(s) encountered failures in {region}")
        
    if not failed and len(filtered_models) == 0 and len(model_to_profiles) == 0 and len(mantle_model_apis) == 0:
        print(f"  ⚠ Region {region} returned 0 models across all APIs; marking as failed.")
        failed = True
    
    return region, filtered_models, model_to_profiles, excluded_count, mantle_model_apis, failed, failed_probe_models


def scan_all_regions_parallel() -> tuple[Dict[str, Any], Set[str], Set[tuple[str, str]]]:
    """
    Scan all AWS regions in parallel and build a mapping of model IDs to regions and inference types.
    
    Returns:
        Tuple of (model_mapping dictionary, set of failed_regions, set of failed_model_regions)
    """
    bedrock_regions = [r for r in get_bedrock_regions() if r not in  ["me-south-1", "me-central-1"]]
    print(f"Scanning {len(bedrock_regions)} Bedrock-enabled regions in parallel...")
    print(f"Regions: {', '.join(bedrock_regions)}\n")
    
    # Structure: model_id -> {regions, inference_types, ...}
    model_mapping = defaultdict(lambda: {
        'regions': [], 
        'inference_types': {}, 
        'model_lifecycle_status': 'ACTIVE',
        'inferenceProfile': {},
        'inputModalities': set(),
        'outputModalities': set(),
        'responseStreamingSupported': None,
        'customizationsSupported': set(),
        'mantle_supported_regions': [],
        'mantle_apis': [],
        'runtime_supported': False
    })
    
    failed_regions = set()
    failed_model_regions = set()
    total_excluded = 0
    lock = threading.Lock()
    
    # Process all regions in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_region = {executor.submit(process_region, region): region for region in bedrock_regions}
        
        for future in as_completed(future_to_region):
            region = future_to_region[future]
            try:
                region_name, models, model_to_profiles, excluded_count, mantle_model_apis, failed, failed_probe_models = future.result()
                
                with lock:
                    if failed:
                        failed_regions.add(region)
                    for m_id in failed_probe_models:
                        failed_model_regions.add((m_id, region))
                        
                    total_excluded += excluded_count
                    
                    for model in models:
                        model_id = model.get('modelId')
                        if not model_id:
                            continue
                        
                        model_lifecycle_status = model.get('modelLifecycle', {}).get('status', 'ACTIVE')
                        model_mapping[model_id]['runtime_supported'] = True
                        
                        # Add region
                        if region not in model_mapping[model_id]['regions']:
                            model_mapping[model_id]['regions'].append(region)
                        
                        # Store lifecycle status
                        if model_mapping[model_id]['model_lifecycle_status'] == 'ACTIVE':
                            model_mapping[model_id]['model_lifecycle_status'] = model_lifecycle_status
                            if model_lifecycle_status == 'LEGACY':
                                print(f"    ⚠ LEGACY model: {model_id}")
                        
                        # Capture modalities, streaming, and customizations
                        input_modalities = model.get('inputModalities', [])
                        output_modalities = model.get('outputModalities', [])
                        streaming_supported = model.get('responseStreamingSupported', False)
                        customizations = model.get('customizationsSupported', [])
                        
                        model_mapping[model_id]['inputModalities'].update(input_modalities)
                        model_mapping[model_id]['outputModalities'].update(output_modalities)
                        
                        # Set streaming to True if any region supports it
                        if streaming_supported:
                            model_mapping[model_id]['responseStreamingSupported'] = True
                        elif model_mapping[model_id]['responseStreamingSupported'] is None:
                            model_mapping[model_id]['responseStreamingSupported'] = False
                        
                        model_mapping[model_id]['customizationsSupported'].update(customizations)
                        
                        # Get base inference types from the model
                        inference_types = list(model.get('inferenceTypesSupported', []))
                        
                        # Replace INFERENCE_PROFILE with actual profile prefixes
                        if 'INFERENCE_PROFILE' in inference_types:
                            # Remove the generic INFERENCE_PROFILE
                            inference_types = [t for t in inference_types if t != 'INFERENCE_PROFILE']
                            
                            # Add the actual profile prefixes for this model
                            if model_id in model_to_profiles:
                                # model_to_profiles is now {model_id: {prefix: [regions]}}
                                prefixes = list(model_to_profiles[model_id].keys())
                                inference_types.extend(prefixes)
                                
                                # Update global inferenceProfile registry for this model
                                for prefix, covered_regions in model_to_profiles[model_id].items():
                                    if prefix == 'GLOBAL':
                                        # GLOBAL is a list of all regions covered across all source regions
                                        existing = set(model_mapping[model_id]['inferenceProfile'].get('GLOBAL', []))
                                        existing.update(covered_regions)
                                        model_mapping[model_id]['inferenceProfile']['GLOBAL'] = sorted(list(existing))
                                    else:
                                        # Regional profiles are now keyed by Source Region
                                        # Structure: prefix -> { source_region -> [covered_regions] }
                                        if prefix not in model_mapping[model_id]['inferenceProfile']:
                                            model_mapping[model_id]['inferenceProfile'][prefix] = {}
                                        
                                        # Current 'region' is the source region
                                        model_mapping[model_id]['inferenceProfile'][prefix][region] = sorted(list(covered_regions))

                        # Store inference types for this region
                        model_mapping[model_id]['inference_types'][region] = inference_types
                        
                    # Merge mantle models and their supported APIs
                    for m, apis in mantle_model_apis.items():
                        # Handle Mantle-only models by initializing with defaults
                        if m not in model_mapping:
                            model_mapping[m]['model_lifecycle_status'] = 'ACTIVE'
                            model_mapping[m]['inputModalities'] = {'TEXT'}
                            # Special handling: if model name hints multimodal, add IMAGE/VIDEO
                            if any(kw in m.lower() for kw in ['-vl', '-vision', 'canvas', 'multimodal']):
                                model_mapping[m]['inputModalities'].update(['IMAGE', 'VIDEO'])
                            model_mapping[m]['outputModalities'] = {'TEXT'}
                            model_mapping[m]['responseStreamingSupported'] = True
                            
                        # Add region to standard regions
                        if region not in model_mapping[m]['regions']:
                            model_mapping[m]['regions'].append(region)
                            
                        # Ensure it has ON_DEMAND in inference_types for this region
                        if region not in model_mapping[m]['inference_types']:
                            model_mapping[m]['inference_types'][region] = ['ON_DEMAND']
                        elif 'ON_DEMAND' not in model_mapping[m]['inference_types'][region]:
                            model_mapping[m]['inference_types'][region].append('ON_DEMAND')
                            
                        # Add region to mantle_supported_regions
                        if region not in model_mapping[m]['mantle_supported_regions']:
                            model_mapping[m]['mantle_supported_regions'].append(region)
                            
                        # Merge/set mantle_apis
                        for api in apis:
                            if api not in model_mapping[m]['mantle_apis']:
                                model_mapping[m]['mantle_apis'].append(api)
                
            except Exception as e:
                print(f"Error processing region {region}: {e}")
                failed_regions.add(region)
    
    print(f"\nTotal excluded models across all regions: {total_excluded}")
    if failed_regions:
        print(f"Failed regions detected during scan: {', '.join(sorted(failed_regions))}")
    if failed_model_regions:
        print(f"Failed model probes detected: {len(failed_model_regions)} (model, region) pairs")
    
    return dict(model_mapping), failed_regions, failed_model_regions


def print_summary(model_mapping: Dict[str, Any]):
    """Print a summary of the model mapping."""
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    legacy_count = sum(1 for data in model_mapping.values() 
                      if data.get('model_lifecycle_status') == 'LEGACY')
    print(f"\nTotal unique models found: {len(model_mapping)}")
    print(f"Legacy models: {legacy_count}\n")
    
    for model_id, data in sorted(model_mapping.items()):
        regions = data['regions']
        lifecycle = data.get('model_lifecycle_status', 'ACTIVE')
        lifecycle_marker = " [LEGACY]" if lifecycle == 'LEGACY' else ""
        
        print(f"\nModel: {model_id}{lifecycle_marker}")
        print(f"  Available in {len(regions)} region(s): {', '.join(sorted(regions))}")
        
        # Print modalities and capabilities
        input_mods = sorted(list(data.get('inputModalities', set())))
        output_mods = sorted(list(data.get('outputModalities', set())))
        streaming = data.get('responseStreamingSupported', False)
        customizations = sorted(list(data.get('customizationsSupported', set())))
        
        print(f"  Input: {', '.join(input_mods) if input_mods else 'N/A'}")
        print(f"  Output: {', '.join(output_mods) if output_mods else 'N/A'}")
        print(f"  Streaming: {'Yes' if streaming else 'No'}")
        if customizations:
            print(f"  Customizations: {', '.join(customizations)}")
        
        # Print inference profiles if any
        if data.get('inferenceProfile'):
            print("  Inference Profiles:")
            for prefix, content in data['inferenceProfile'].items():
                if prefix == 'GLOBAL':
                    print(f"    {prefix}: {content}")
                else:
                    print(f"    {prefix}:")
                    for src, covered in content.items():
                        print(f"      From {src}: {covered}")
                        
        # Print Mantle info if any
        if data.get('mantle_supported_regions'):
            print(f"  Mantle Supported Regions: {', '.join(sorted(data['mantle_supported_regions']))}")
            print(f"  Mantle Supported APIs: {', '.join(sorted(data['mantle_apis']))}")
        
        print(f"  Inference types by region:")
        for region in sorted(regions):
            inference_types = data['inference_types'].get(region, [])
            print(f"    {region}: {', '.join(inference_types)}")


def merge_failed_regions_from_previous(
    sorted_mapping: Dict[str, Any],
    failed_regions: Set[str] | None,
    old_models: Dict[str, Any],
    failed_model_regions: Set[tuple[str, str]] | None = None,
) -> None:
    """
    If any region or specific model probe failed during scanning (e.g. due to API throttling or timeouts),
    preserve the previous known-good state for that region/model from old_models instead of
    assuming models/features in that region were removed.
    """
    if not old_models:
        return

    failed_regions = failed_regions or set()
    failed_model_regions = failed_model_regions or set()

    if failed_regions:
        print(f"Preserving previous state for failed regions: {', '.join(sorted(failed_regions))}")

    # 1. Process entire failed regions
    for region in sorted(failed_regions):
        for model_id, old_entry in old_models.items():
            old_regions = old_entry.get('regions', [])
            old_inf_types = old_entry.get('inference_types', {})
            old_mantle_regions = old_entry.get('mantle_supported_regions', [])
            old_inf_profile = old_entry.get('inferenceProfile', {})

            was_in_regions = region in old_regions
            was_in_inf_types = region in old_inf_types
            was_in_mantle = region in old_mantle_regions

            has_profile_src = False
            for prefix, content in old_inf_profile.items():
                if prefix != 'GLOBAL' and isinstance(content, dict) and region in content:
                    has_profile_src = True
                    break

            if not (was_in_regions or was_in_inf_types or was_in_mantle or has_profile_src):
                continue

            if model_id not in sorted_mapping:
                print(f"  Restoring model {model_id} from old state because region {region} failed")
                import copy
                sorted_mapping[model_id] = copy.deepcopy(old_entry)
                continue

            entry = sorted_mapping[model_id]

            if was_in_regions and region not in entry['regions']:
                print(f"  Restoring region {region} for model {model_id}")
                entry['regions'].append(region)
                entry['regions'].sort()

            if was_in_inf_types:
                if region not in entry['inference_types']:
                    print(f"  Restoring inference_types for region {region} on model {model_id}")
                    entry['inference_types'][region] = sorted(old_inf_types[region])
                else:
                    current_types = set(entry['inference_types'][region])
                    missing_types = set(old_inf_types[region]) - current_types
                    if missing_types:
                        print(f"  Restoring missing inference_types {sorted(list(missing_types))} for region {region} on model {model_id}")
                        current_types.update(missing_types)
                        entry['inference_types'][region] = sorted(list(current_types))

            if was_in_mantle:
                if 'mantle_supported_regions' not in entry:
                    entry['mantle_supported_regions'] = []
                if region not in entry['mantle_supported_regions']:
                    print(f"  Restoring mantle_supported_regions {region} for model {model_id}")
                    entry['mantle_supported_regions'].append(region)
                    entry['mantle_supported_regions'].sort()

                old_mantle_apis = old_entry.get('mantle_apis', [])
                if old_mantle_apis:
                    if 'mantle_apis' not in entry:
                        entry['mantle_apis'] = sorted(old_mantle_apis)
                    else:
                        current_apis = set(entry['mantle_apis'])
                        missing_apis = set(old_mantle_apis) - current_apis
                        if missing_apis:
                            current_apis.update(missing_apis)
                            entry['mantle_apis'] = sorted(list(current_apis))

            if has_profile_src:
                if 'inferenceProfile' not in entry:
                    entry['inferenceProfile'] = {}
                for prefix, content in old_inf_profile.items():
                    if prefix != 'GLOBAL' and isinstance(content, dict) and region in content:
                        if prefix not in entry['inferenceProfile']:
                            entry['inferenceProfile'][prefix] = {}
                        if region not in entry['inferenceProfile'][prefix]:
                            print(f"  Restoring inferenceProfile {prefix} for source region {region} on model {model_id}")
                            entry['inferenceProfile'][prefix][region] = sorted(content[region])

            if 'GLOBAL' in old_inf_profile and isinstance(old_inf_profile['GLOBAL'], list):
                if region in old_inf_profile['GLOBAL']:
                    if 'inferenceProfile' not in entry:
                        entry['inferenceProfile'] = {}
                    if 'GLOBAL' not in entry['inferenceProfile']:
                        entry['inferenceProfile']['GLOBAL'] = [region]
                    elif region not in entry['inferenceProfile']['GLOBAL']:
                        entry['inferenceProfile']['GLOBAL'].append(region)
                        entry['inferenceProfile']['GLOBAL'].sort()

    # 2. Process specific (model, region) probe failures
    for model_id, region in sorted(failed_model_regions):
        if model_id in old_models:
            old_entry = old_models[model_id]
            old_regions = old_entry.get('regions', [])
            old_inf_types = old_entry.get('inference_types', {}).get(region, [])
            old_mantle_regions = old_entry.get('mantle_supported_regions', [])

            was_in_regions = region in old_regions

            if model_id not in sorted_mapping:
                print(f"  Restoring model {model_id} from old state due to probe failure in region {region}")
                import copy
                sorted_mapping[model_id] = copy.deepcopy(old_entry)
                continue

            entry = sorted_mapping[model_id]

            # Restore region in regions list
            if was_in_regions and region not in entry['regions']:
                print(f"  Restoring region {region} for model {model_id} due to probe failure")
                entry['regions'].append(region)
                entry['regions'].sort()

            # Restore missing ON_DEMAND / inference types for this region
            if old_inf_types:
                if region not in entry['inference_types']:
                    entry['inference_types'][region] = sorted(old_inf_types)
                    print(f"  Restoring inference_types for model {model_id} in region {region} due to probe failure")
                else:
                    current_types = set(entry['inference_types'][region])
                    missing_types = set(old_inf_types) - current_types
                    if missing_types:
                        print(f"  Restoring missing inference_types {sorted(list(missing_types))} for model {model_id} in region {region} due to probe failure")
                        current_types.update(missing_types)
                        entry['inference_types'][region] = sorted(list(current_types))

            # Restore mantle_supported_regions for this region
            if region in old_mantle_regions:
                if 'mantle_supported_regions' not in entry:
                    entry['mantle_supported_regions'] = []
                if region not in entry['mantle_supported_regions']:
                    print(f"  Restoring mantle_supported_regions {region} for model {model_id} due to probe failure")
                    entry['mantle_supported_regions'].append(region)
                    entry['mantle_supported_regions'].sort()

            old_mantle_apis = old_entry.get('mantle_apis', [])
            if old_mantle_apis:
                if 'mantle_apis' not in entry:
                    entry['mantle_apis'] = sorted(old_mantle_apis)
                else:
                    current_apis = set(entry['mantle_apis'])
                    missing_apis = set(old_mantle_apis) - current_apis
                    if missing_apis:
                        current_apis.update(missing_apis)
                        entry['mantle_apis'] = sorted(list(current_apis))


def save_to_json(
    model_mapping: Dict[str, Any],
    filename: str = '../shared/bedrock_models.json',
    failed_regions: Set[str] | None = None,
    failed_model_regions: Set[tuple[str, str]] | None = None,
):
    """Save the model mapping to a JSON file with sorted keys and values for deterministic output."""
    import os
    import json
    from datetime import datetime, timezone

    # Sort regions and inference_types lists for deterministic output
    sorted_mapping = {}
    for model_id in sorted(model_mapping.keys()):
        data = model_mapping[model_id]
        
        entry = {
            'regions': sorted(data['regions']),
            'inference_types': {region: sorted(types) for region, types in sorted(data['inference_types'].items())},
            'model_lifecycle_status': data.get('model_lifecycle_status', 'ACTIVE'),
            'inputModalities': sorted(list(data.get('inputModalities', set()))),
            'outputModalities': sorted(list(data.get('outputModalities', set()))),
            'responseStreamingSupported': data.get('responseStreamingSupported', False),
            'customizationsSupported': sorted(list(data.get('customizationsSupported', set())))
        }
        
        # Add runtime support if applicable
        if data.get('runtime_supported'):
            entry['runtime_supported'] = True

        # Add inferenceProfile if it exists and is not empty
        if data.get('inferenceProfile'):
            entry['inferenceProfile'] = {}
            for prefix, content in sorted(data['inferenceProfile'].items()):
                if prefix == 'GLOBAL':
                    entry['inferenceProfile'][prefix] = sorted(content)
                else:
                    entry['inferenceProfile'][prefix] = {
                        src: sorted(tgts) for src, tgts in sorted(content.items())
                    }
                    
        # Add mantle fields if supported
        if data.get('mantle_supported_regions'):
            entry['mantle_supported_regions'] = sorted(data['mantle_supported_regions'])
            entry['mantle_apis'] = sorted(data['mantle_apis'])
            
        sorted_mapping[model_id] = entry
    
    # Load old model definitions to compare
    old_models = {}
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                old_models = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load existing models file: {e}")

    # Preserve previous state for failed regions or failed model probes
    if (failed_regions or failed_model_regions) and old_models:
        merge_failed_regions_from_previous(sorted_mapping, failed_regions, old_models, failed_model_regions)

    # Load existing metadata
    metadata_filename = os.path.join(os.path.dirname(filename), 'bedrock_models_metadata.json')
    old_metadata = {}
    if os.path.exists(metadata_filename):
        try:
            with open(metadata_filename, 'r') as f:
                old_metadata = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load existing metadata file: {e}")

    current_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    new_metadata = {}

    # 1. Process all active models in the new mapping
    for model_id, entry in sorted_mapping.items():
        old_entry = old_models.get(model_id)
        existing_meta = old_metadata.get(model_id, {})
        
        # Check if the model is new OR its definition has changed
        if old_entry is None or entry != old_entry:
            new_metadata[model_id] = {
                'last_changed': current_date
            }
        else:
            # Definition hasn't changed. Keep previous last_changed, or fallback to current_date if missing.
            last_changed = existing_meta.get('last_changed', current_date)
            new_metadata[model_id] = {
                'last_changed': last_changed
            }

    # 2. Process models that were in the old models OR old metadata but are not in the new mapping
    all_past_model_ids = set(old_models.keys()) | set(old_metadata.keys())
    deleted_model_ids = all_past_model_ids - set(sorted_mapping.keys())
    
    for model_id in sorted(deleted_model_ids):
        existing_meta = old_metadata.get(model_id, {})
        last_changed = existing_meta.get('last_changed', current_date)
        deleted_date = existing_meta.get('deleted')
        
        # If it was already marked deleted, keep that date. Otherwise, set it to current_date.
        if not deleted_date:
            deleted_date = current_date
            
        new_metadata[model_id] = {
            'last_changed': last_changed,
            'deleted': deleted_date
        }

    # Write bedrock_models.json
    with open(filename, 'w') as f:
        json.dump(sorted_mapping, f, indent=2)
    print(f"\nSaved model definitions to {filename}")

    # Write bedrock_models_metadata.json
    with open(metadata_filename, 'w') as f:
        json.dump(new_metadata, f, indent=2)
    print(f"Saved metadata definitions to {metadata_filename}")


def main():
    """Main execution function."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    
    print("="*80)
    print("AWS Bedrock Model Scanner")
    print("="*80 + "\n")
    
    # Scan all regions
    model_mapping, failed_regions, failed_model_regions = scan_all_regions_parallel()
    
    # Print summary
    print_summary(model_mapping)
    
    # Save to JSON file
    save_to_json(model_mapping, failed_regions=failed_regions, failed_model_regions=failed_model_regions)


if __name__ == '__main__':
    main()
