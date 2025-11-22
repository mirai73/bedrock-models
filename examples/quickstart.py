#!/usr/bin/env python3
"""
Quick start example for bedrock-models library.
"""

from bedrock_models import (
    Models,
    cris_model_id,
    is_model_available,
    get_available_regions,
)

# 1. Get a model ID with autocomplete
model = Models.ANTHROPIC_CLAUDE_3_5_SONNET_20241022
print(f"Model ID: {model}")

# 2. Check if available in your region
region = "us-east-1"
if is_model_available(model, region):
    print(f"✓ Available in {region}")
    
    # 3. Get the best CRIS ID (automatically chooses geo or global)
    model_id = cris_model_id(model, region=region)
    print(f"CRIS ID: {model_id}")
else:
    print(f"✗ Not available in {region}")
    
    # Find where it's available
    regions = get_available_regions(model)
    print(f"Available in: {', '.join(regions[:5])}")
