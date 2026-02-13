# Bedrock Models

[![PyPI version](https://badge.fury.io/py/bedrock-models.svg)](https://badge.fury.io/py/bedrock-models)

A Python library that provides AWS Bedrock Foundation Model IDs with autocomplete support and utility functions for cross-region inference.

This library helps developer to easily use Bedrock foundation models without having to lookup the model id or the correct cris profile prefix to use. The list of models is checked and updated daily.

## 🌐 [Browse Models Online](https://mirai73.github.io/bedrock-models/)

Explore all available Bedrock models with our interactive web interface. Search by model name, filter by region, and find CRIS-enabled models.

## Features

- **Type-safe model IDs**: Access all Bedrock model IDs as Python constants with full autocomplete support
- **Cross-region inference**: Automatically generate CRIS (Cross-Region Inference Service) prefixed model IDs
- **Region validation**: Check model availability across AWS regions
- **Auto-updated**: Model IDs are automatically updated weekly from AWS Bedrock API

## Installation

```bash
pip install bedrock-models
```

## Quick Start

The following code is portable across regions without any change

```python
import boto3
from bedrock_models import Models, cris_model_id, global_model_id


client = boto3.client('bedrock-runtime')

# Get model ID with autocomplete
model = Models.ANTHROPIC_CLAUDE_HAIKU_4_5_20251001

# The correct geo profile id is determined from the boto3 default region
# regional geo profile is preferred, and falls back to global profile
client.converse(modelId=cris_model_id(model), messages=[...])

# To force a global profile, if available in the region, use global_model_id
client.converse(modelId=global_model_id(model), messages=[...])

```

## Usage

### Basic Model IDs

```python
from bedrock_models import Models

# Access model IDs with autocomplete
model_id = Models.ANTHROPIC_CLAUDE_3_5_SONNET_20241022
# Returns: "anthropic.claude-3-5-sonnet-20241022-v2:0"

model_id = Models.AMAZON_NOVA_PRO
# Returns: "amazon.nova-pro-v1:0"
```

### Cross-Region Inference (CRIS)

```python
from bedrock_models import Models, cris_model_id

# Get CRIS model ID (automatically chooses geo or global based on availability)
cris_id = cris_model_id(
    Models.ANTHROPIC_CLAUDE_3_5_SONNET_20241022,
    region="us-east-1"
)
# Returns: "us.anthropic.claude-3-5-sonnet-20241022-v2:0" (geo CRIS if INFERENCE_PROFILE available)
# Or: "global.anthropic.claude-3-5-sonnet-20241022-v2:0" (if only GLOBAL available)

# Different region prefix (AP regions use "apac")
cris_id = cris_model_id(
    Models.AMAZON_NOVA_PRO,
    region="ap-south-1"
)
# Returns: "apac.amazon.nova-pro-v1:0"

# Auto-detect region from boto3 (if installed and configured)
# AWS_DEFAULT_REGION=us-west-2
import boto3

cris_id = cris_model_id(
    Models.AMAZON_NOVA_PRO  # region auto-detected from boto3
)
# Returns: "us.amazon.nova-pro-v1:0"
```

### Check Model Availability

```python
from bedrock_models import Models, is_model_available, get_available_regions

# Check if a model is available in a specific region
available = is_model_available(Models.AMAZON_NOVA_PRO, "us-west-2")
# Returns: True or False

# Auto-detect region from boto3 (if installed and configured)
available = is_model_available(Models.AMAZON_NOVA_PRO)
# Uses region from boto3 session

# Get all regions where a model is available
regions = get_available_regions(Models.ANTHROPIC_CLAUDE_3_5_SONNET_20241022)
# Returns: ['us-east-1', 'us-west-2', 'ap-south-1', ...]
```

### Inference Profiles

```python
from bedrock_models import (
    Models,
    cris_model_id,
    global_model_id,
    has_global_profile,
)

# Get CRIS model ID (automatically chooses geo or global based on availability)
model_id = cris_model_id(Models.ANTHROPIC_CLAUDE_3_5_SONNET_20241022, region="us-east-1")
# Returns: "us.anthropic.claude-3-5-sonnet-20241022-v2:0" (geo CRIS)
# Or: "global.anthropic.claude-3-5-sonnet-20241022-v2:0" (if only global available)

# Get global inference profile ID (if supported in region)
global_id = global_model_id(Models.AMAZON_NOVA_PRO, region="us-east-1")
# Returns: "global.amazon.nova-pro-v1:0"
# Raises ValueError if global profile not supported in region

# Check if a model has a global inference profile in a region
has_global = has_global_profile(
    Models.ANTHROPIC_CLAUDE_3_5_SONNET_20241022,
    "us-east-1"
)
# Returns: True or False
```

## Development

### Setup

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Run tests
poetry run pytest
```

### Regenerate Model IDs

To update the model IDs from AWS Bedrock:

```bash
# Set AWS credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Generate model data from AWS
python utils/generate_models_json.py

# Generate Python class
python utils/generate_model_class.py

# Run tests
poetry run pytest
```

### Required IAM Permissions

The AWS credentials need the following least-privilege IAM policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockReadOnly",
      "Effect": "Allow",
      "Action": [
        "bedrock:ListFoundationModels",
        "bedrock:ListInferenceProfiles"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EC2DescribeRegions",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeRegions"
      ],
      "Resource": "*"
    }
  ]
}
```



## Credits

This project uses the following open-source libraries and data in the github pages site:

-   **[Leaflet](https://leafletjs.com/)**: An open-source JavaScript library for mobile-friendly interactive maps. Copyright (c) 2010-2023, Volodymyr Agafonkin.
-   **[OpenStreetMap](https://www.openstreetmap.org/)**: Map data © OpenStreetMap contributors.

## License

MIT-0

## Author

Massimiliano Angelino <massi.ang@gmail.com>
