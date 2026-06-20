#!/usr/bin/env python3
"""
Script to scan all AWS regions and retrieve foundation model IDs available in each region.
Maps each unique model ID to the list of regions where it's supported and the inference types.
Uses ThreadPoolExecutor for parallel processing to speed up scanning.
"""

import boto3
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set, Any
import threading
import urllib.request
import urllib.error
from aws_bedrock_token_generator import provide_token


def get_bedrock_regions() -> List[str]:
    """Get regions where Bedrock service is available."""
    session = boto3.Session()
    return session.get_available_regions('bedrock')


def get_foundation_models_in_region(region: str) -> tuple[str, List[Dict]]:
    """
    Get all foundation models available in a specific region.
    
    Args:
        region: AWS region name
        
    Returns:
        Tuple of (region, list of model dictionaries)
    """
    try:
        bedrock = boto3.client('bedrock', region_name=region)
        response = bedrock.list_foundation_models()
        return region, response.get('modelSummaries', [])
    except Exception as e:
        print(f"Error accessing region {region}: {e}")
        return region, []


def get_inference_profiles_in_region(region: str) -> Dict[str, Dict[str, List[str]]]:
    """
    Get all inference profiles available in a specific region and their covered regions.
    Maps model IDs to a dictionary of profile prefixes and their covered regions.
    
    Args:
        region: AWS region name
        
    Returns:
        Dictionary mapping model IDs to profile info:
        {
            "model.id": {
                "US": ["us-east-1", "us-west-2"],
                "EU": ["eu-central-1"]
            }
        }
    """
    try:
        bedrock = boto3.client('bedrock', region_name=region)
        response = bedrock.list_inference_profiles()
        
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
                    details = bedrock.get_inference_profile(inferenceProfileIdentifier=profile_id)
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
        return {}


def get_mantle_models_in_region(region: str) -> Dict[str, List[str]]:
    """
    Query all models on the Bedrock Mantle endpoint in a specific region,
    and probe their support for completions and responses endpoints using validation-only check.
    
    Returns:
        Dict mapping model ID -> list of supported APIs: e.g., {'model_id': ['completions', 'responses']}
    """
    try:
        token = provide_token(region=region)
    except Exception as e:
        print(f"  ⚠ Could not generate Mantle token for {region}: {e}")
        return {}
        
    url_models = f"https://bedrock-mantle.{region}.api.aws/v1/models"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url_models, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            model_ids = [m['id'] for m in data.get('data', [])]
    except Exception:
        # If the endpoint doesn't exist or isn't reachable (e.g. host name unresolved), return empty dict
        return {}
        
    def probe_model(model_id):
        supported_apis = []
        
        # 1. Probe completions API
        if not model_id.startswith('anthropic.'):
            url_comp = f"https://bedrock-mantle.{region}.api.aws/v1/chat/completions"
            payload_comp = {
                "model": model_id,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": -1
            }
            req_comp = urllib.request.Request(url_comp, data=json.dumps(payload_comp).encode(), headers=headers, method='POST')
            try:
                with urllib.request.urlopen(req_comp, timeout=5) as r:
                    pass
            except urllib.error.HTTPError as e:
                body = e.read().decode()
                if 'max_tokens' in body or 'access_denied' in body:
                    supported_apis.append('completions')
            except Exception:
                pass
            
        # 2. Probe responses API
        if not model_id.startswith('anthropic.'):
            url_resp = f"https://bedrock-mantle.{region}.api.aws/v1/responses"
            payload_resp = {
                "model": model_id,
                "input": "hi",
                "max_output_tokens": -1,
                "store": False
            }
            req_resp = urllib.request.Request(url_resp, data=json.dumps(payload_resp).encode(), headers=headers, method='POST')
            try:
                with urllib.request.urlopen(req_resp, timeout=5) as r:
                    pass
            except urllib.error.HTTPError as e:
                body = e.read().decode()
                if 'max_output_tokens' in body or 'access_denied' in body:
                    supported_apis.append('responses')
            except Exception:
                pass
            
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
                with urllib.request.urlopen(req_msg, timeout=5) as r:
                    pass
            except urllib.error.HTTPError as e:
                body = e.read().decode()
                if 'max_tokens' in body or 'access_denied' in body:
                    supported_apis.append('messages')
            except Exception:
                pass
            
        return model_id, sorted(supported_apis) if supported_apis else None

    model_apis = {}
    with ThreadPoolExecutor(max_workers=10) as inner_executor:
        futures = [inner_executor.submit(probe_model, m) for m in model_ids]
        for f in as_completed(futures):
            res = f.result()
            if res and res[1]:
                model_apis[res[0]] = res[1]
                
    return model_apis


def process_region(region: str) -> tuple[str, List[Dict], Dict[str, Dict[str, List[str]]], int, Dict[str, List[str]]]:
    """
    Process a single region: get models, inference profiles, and Mantle models.
    
    Args:
        region: AWS region name
        
    Returns:
        Tuple of (region, filtered_models, model_to_profiles, excluded_count, mantle_model_apis)
    """
    print(f"Scanning region: {region}")
    region_name, models = get_foundation_models_in_region(region)
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
    
    if model_to_profiles:
        count = sum(len(profiles) for profiles in model_to_profiles.values())
        print(f"  Found {count} profile definitions")
        
    # Get all Bedrock Mantle models and their supported APIs
    print(f"  Probing Bedrock Mantle models in {region}...")
    mantle_model_apis = get_mantle_models_in_region(region)
    print(f"  Found {len(mantle_model_apis)} Mantle-supported models in {region}")
    
    return region, filtered_models, model_to_profiles, excluded_count, mantle_model_apis


def scan_all_regions_parallel() -> Dict[str, Any]:
    """
    Scan all AWS regions in parallel and build a mapping of model IDs to regions and inference types.
    
    Returns:
        Dictionary mapping model IDs to their supported regions and inference types
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
    
    total_excluded = 0
    lock = threading.Lock()
    
    # Process all regions in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_region = {executor.submit(process_region, region): region for region in bedrock_regions}
        
        for future in as_completed(future_to_region):
            region = future_to_region[future]
            try:
                region_name, models, model_to_profiles, excluded_count, mantle_model_apis = future.result()
                
                with lock:
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
    
    print(f"\nTotal excluded models across all regions: {total_excluded}")
    
    return dict(model_mapping)


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


def save_to_json(model_mapping: Dict[str, Any], filename: str = '../shared/bedrock_models.json'):
    """Save the model mapping to a JSON file with sorted keys and values for deterministic output."""
    import os
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
        json.dump(sorted_mapping, f, indent=2, sort_keys=True)
    print(f"\n\nResults saved to {filename}")

    # Write bedrock_models_metadata.json
    with open(metadata_filename, 'w') as f:
        json.dump(new_metadata, f, indent=2, sort_keys=True)
    print(f"Metadata saved to {metadata_filename}")


def main():
    """Main function to scan regions and generate model mapping."""
    print("AWS Bedrock Foundation Model Scanner (Parallel)")
    print("="*80 + "\n")
    
    # Scan all regions
    model_mapping = scan_all_regions_parallel()
    
    # Print summary
    print_summary(model_mapping)
    
    # Save to JSON file
    save_to_json(model_mapping)


if __name__ == '__main__':
    main()
