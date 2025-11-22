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
from typing import Dict, List
import threading


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


def get_inference_profiles_in_region(region: str) -> Dict[str, List[str]]:
    """
    Get all inference profiles available in a specific region.
    Maps model IDs to their available profile prefixes (EU, US, GLOBAL, CA, etc.)
    
    Args:
        region: AWS region name
        
    Returns:
        Dictionary mapping model IDs to list of profile prefixes
    """
    try:
        bedrock = boto3.client('bedrock', region_name=region)
        response = bedrock.list_inference_profiles()
        
        model_profiles = defaultdict(list)
        
        for profile in response.get('inferenceProfileSummaries', []):
            profile_id = profile.get('inferenceProfileId', '')
            
            # Extract prefix from profile ID (e.g., "us.anthropic.claude-3-5-sonnet-20240620-v1:0" -> "US")
            if '.' in profile_id:
                prefix = profile_id.split('.')[0].upper()
                model_id  = '.'.join(profile_id.split('.')[1:])
                model_profiles[model_id].append(prefix)
        
        return dict(model_profiles)
    except Exception as e:
        print(f"  Error listing inference profiles in {region}: {e}")
        return {}


def process_region(region: str) -> tuple[str, List[Dict], Dict[str, List[str]], int]:
    """
    Process a single region: get models and inference profiles.
    
    Args:
        region: AWS region name
        
    Returns:
        Tuple of (region, filtered_models, model_to_profiles, excluded_count)
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
            print(f"    ⓧ Excluding {model_id} (only PROVISIONED)")
    
    print(f"  Kept {len(filtered_models)} models after filtering")
    
    # Get all inference profiles in this region
    model_to_profiles = get_inference_profiles_in_region(region)
    
    if model_to_profiles:
        print(f"  Found inference profiles for {len(model_to_profiles)} models")
        for model_id, prefixes in model_to_profiles.items():
            print(f"    ✓ {model_id}: {', '.join(prefixes)}")
    
    return region, filtered_models, model_to_profiles, excluded_count


def scan_all_regions_parallel() -> Dict[str, Dict[str, List[str]]]:
    """
    Scan all AWS regions in parallel and build a mapping of model IDs to regions and inference types.
    
    Returns:
        Dictionary mapping model IDs to their supported regions and inference types
    """
    bedrock_regions = get_bedrock_regions()
    print(f"Scanning {len(bedrock_regions)} Bedrock-enabled regions in parallel...")
    print(f"Regions: {', '.join(bedrock_regions)}\n")
    
    model_mapping = defaultdict(lambda: {'regions': [], 'inference_types': {}, 'model_lifecycle_status': 'ACTIVE'})
    total_excluded = 0
    lock = threading.Lock()
    
    # Process all regions in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_region = {executor.submit(process_region, region): region for region in bedrock_regions}
        
        for future in as_completed(future_to_region):
            region = future_to_region[future]
            try:
                region_name, models, model_to_profiles, excluded_count = future.result()
                
                with lock:
                    total_excluded += excluded_count
                    
                    for model in models:
                        model_id = model.get('modelId')
                        if not model_id:
                            continue
                        
                        model_lifecycle_status = model.get('modelLifecycle', {}).get('status', 'ACTIVE')
                        
                        # Add region
                        if region not in model_mapping[model_id]['regions']:
                            model_mapping[model_id]['regions'].append(region)
                        
                        # Store lifecycle status
                        if model_mapping[model_id]['model_lifecycle_status'] == 'ACTIVE':
                            model_mapping[model_id]['model_lifecycle_status'] = model_lifecycle_status
                            if model_lifecycle_status == 'LEGACY':
                                print(f"    ⚠ LEGACY model: {model_id}")
                        
                        # Get base inference types from the model
                        inference_types = list(model.get('inferenceTypesSupported', []))
                        
                        # Replace INFERENCE_PROFILE with actual profile prefixes
                        if 'INFERENCE_PROFILE' in inference_types:
                            # Remove the generic INFERENCE_PROFILE
                            inference_types = [t for t in inference_types if t != 'INFERENCE_PROFILE']
                            
                            # Add the actual profile prefixes for this model
                            if model_id in model_to_profiles:
                                inference_types.extend(model_to_profiles[model_id])
                        
                        # Store inference types for this region
                        model_mapping[model_id]['inference_types'][region] = inference_types
                
            except Exception as e:
                print(f"Error processing region {region}: {e}")
    
    print(f"\nTotal excluded models across all regions: {total_excluded}")
    
    return dict(model_mapping)


def print_summary(model_mapping: Dict[str, Dict[str, List[str]]]):
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
        print(f"  Inference types by region:")
        for region in sorted(regions):
            inference_types = data['inference_types'].get(region, [])
            print(f"    {region}: {', '.join(inference_types)}")


def save_to_json(model_mapping: Dict[str, Dict[str, List[str]]], filename: str = 'bedrock_models/bedrock_models.json'):
    """Save the model mapping to a JSON file with sorted keys and values for deterministic output."""
    # Sort regions and inference_types lists for deterministic output
    sorted_mapping = {}
    for model_id in sorted(model_mapping.keys()):
        data = model_mapping[model_id]
        sorted_mapping[model_id] = {
            'regions': sorted(data['regions']),
            'inference_types': {region: sorted(types) for region, types in sorted(data['inference_types'].items())},
            'model_lifecycle_status': data.get('model_lifecycle_status', 'ACTIVE')
        }
    
    with open(filename, 'w') as f:
        json.dump(sorted_mapping, f, indent=2, sort_keys=True)
    print(f"\n\nResults saved to {filename}")


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
