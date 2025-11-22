#!/usr/bin/env python3
"""
Example usage of the bedrock-models library.

This script demonstrates how to use the various functions to work with
AWS Bedrock model IDs, check availability, and generate cross-region
inference profile IDs.
"""

from bedrock_models import (
    Models,
    is_model_available,
    get_available_regions,
    has_global_profile,
    cris_model_id,
)


def example_basic_model_ids():
    """Example: Access model IDs with autocomplete."""
    print("=" * 80)
    print("BASIC MODEL IDS")
    print("=" * 80)
    
    # Access model IDs as constants
    claude_model = Models.ANTHROPIC_CLAUDE_3_5_SONNET_20241022
    print(f"Claude 3.5 Sonnet: {claude_model}")
    
    nova_model = Models.AMAZON_NOVA_PRO
    print(f"Amazon Nova Pro: {nova_model}")
    
    llama_model = Models.META_LLAMA3_3_70B_INSTRUCT
    print(f"Llama 3.3 70B: {llama_model}")
    print()


def example_cross_region_inference():
    """Example: Generate cross-region inference (CRIS) model IDs."""
    print("=" * 80)
    print("CROSS-REGION INFERENCE (CRIS)")
    print("=" * 80)
    
    model = Models.ANTHROPIC_CLAUDE_3_5_SONNET_20241022
    
    # Get available regions for this model
    available_regions = get_available_regions(model)
    
    # US region
    if "us-east-1" in available_regions:
        us_cris = cris_model_id(model, region="us-east-1")
        print(f"US CRIS ID: {us_cris}")
    
    # APAC region (note: AP regions use 'apac' prefix)
    if "ap-south-1" in available_regions:
        apac_cris = cris_model_id(model, region="ap-south-1")
        print(f"APAC CRIS ID: {apac_cris}")
    
    # Another US region
    if "us-west-2" in available_regions:
        us_west_cris = cris_model_id(model, region="us-west-2")
        print(f"US West CRIS ID: {us_west_cris}")
    
    # Base model ID (without CRIS)
    print(f"Base model ID: {model}")
    print()


def example_check_availability():
    """Example: Check model availability in regions."""
    print("=" * 80)
    print("CHECK MODEL AVAILABILITY")
    print("=" * 80)
    
    model = Models.AMAZON_NOVA_PRO
    
    # Check specific region
    region = "us-west-2"
    available = is_model_available(model, region)
    print(f"Is {model} available in {region}? {available}")
    
    # Get all available regions
    regions = get_available_regions(model)
    print(f"\n{model} is available in {len(regions)} regions:")
    for region in sorted(regions):
        print(f"  - {region}")
    print()


def example_global_profiles():
    """Example: Work with global inference profiles."""
    print("=" * 80)
    print("GLOBAL INFERENCE PROFILES")
    print("=" * 80)
    
    from bedrock_models import global_model_id
    
    model = Models.ANTHROPIC_CLAUDE_3_5_SONNET_20241022
    
    # Check if global profile is available in regions where model exists
    available_regions = get_available_regions(model)
    regions_to_check = available_regions[:3]  # Check first 3 available regions
    
    print(f"Checking global profile availability for {model}:")
    for region in regions_to_check:
        has_global = has_global_profile(model, region)
        status = "✓ Available" if has_global else "✗ Not available"
        print(f"  {region}: {status}")
        
        # Try to get global profile ID if available
        if has_global:
            try:
                global_id = global_model_id(model, region=region)
                print(f"    Global ID: {global_id}")
            except ValueError:
                pass
    print()


def example_practical_use_case():
    """Example: Practical use case - selecting best model endpoint."""
    print("=" * 80)
    print("PRACTICAL USE CASE: Selecting Best Endpoint")
    print("=" * 80)
    
    from bedrock_models import cris_model_id, global_model_id
    
    model = Models.ANTHROPIC_CLAUDE_3_5_SONNET_20241022
    preferred_region = "us-east-1"
    
    print(f"Model: {model}")
    print(f"Preferred region: {preferred_region}")
    
    # Check if model is available in preferred region
    if is_model_available(model, preferred_region):
        print(f"✓ Model is available in {preferred_region}")
        
        # Try to use global profile first (better latency/availability)
        try:
            endpoint_id = global_model_id(model, region=preferred_region)
            print(f"✓ Using global profile: {endpoint_id}")
        except ValueError:
            # Fall back to CRIS (geo or global)
            endpoint_id = cris_model_id(model, region=preferred_region)
            print(f"→ Using CRIS: {endpoint_id}")
    else:
        print(f"✗ Model not available in {preferred_region}")
        # Find alternative regions
        available_regions = get_available_regions(model)
        print(f"Available in: {', '.join(available_regions[:3])}...")
    print()


def example_boto3_integration():
    """Example: Using with boto3 Bedrock client."""
    print("=" * 80)
    print("BOTO3 INTEGRATION EXAMPLE")
    print("=" * 80)
    
    print("Example code for using with boto3:\n")
    
    code = '''
import boto3
from bedrock_models import Models, cris_model_id, global_model_id

# Initialize Bedrock client
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# Select model
model = Models.ANTHROPIC_CLAUDE_3_5_SONNET_20241022

# Choose the best endpoint (try global first, fall back to CRIS)
try:
    model_id = global_model_id(model, region='us-east-1')
except ValueError:
    model_id = cris_model_id(model, region='us-east-1')

# Or simply use cris_model_id which automatically chooses the best option
model_id = cris_model_id(model, region='us-east-1')

# Make API call
response = bedrock.invoke_model(
    modelId=model_id,
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": "Hello!"}
        ]
    })
)
'''
    print(code)


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "BEDROCK MODELS LIBRARY EXAMPLES" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    example_basic_model_ids()
    example_cross_region_inference()
    example_check_availability()
    example_global_profiles()
    example_practical_use_case()
    example_boto3_integration()
    
    print("=" * 80)
    print("For more information, visit: https://github.com/yourusername/bedrock-models")
    print("=" * 80)


if __name__ == "__main__":
    main()
