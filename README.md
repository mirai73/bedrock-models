# Bedrock Models

A Python library that provides AWS Bedrock Foundation Model IDs with autocomplete support and utility functions for cross-region inference.

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

```python
from bedrock_models import Models, cris_model_id, is_model_available

# Get model ID with autocomplete
model = Models.ANTHROPIC_CLAUDE_3_5_SONNET_20241022

# Check availability
if is_model_available(model, "us-east-1"):
    # Get the best CRIS ID (geo or global)
    model_id = cris_model_id(model, region="us-east-1")
    print(model_id)  # us.anthropic.claude-3-5-sonnet-20241022-v2:0
```

See [examples/](examples/) for more detailed usage examples.

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
import boto3
boto3.setup_default_session(region_name='us-west-2')

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
python utils/gen_model_enum.py
mv bedrock_models.json bedrock_models/

# Generate Python class
python utils/generate_model_class.py

# Run tests
poetry run pytest
```

## GitHub Actions Setup

This repository uses GitHub Actions to automatically update model IDs and publish to PyPI.

### Required Secrets

Configure these secrets in your GitHub repository settings (Settings → Secrets and variables → Actions):

1. **AWS_ACCESS_KEY_ID**: AWS access key with Bedrock read permissions
2. **AWS_SECRET_ACCESS_KEY**: AWS secret access key
3. **PYPI_TOKEN**: PyPI API token for publishing packages

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
        "bedrock:GetInferenceProfile"
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

- `bedrock:ListFoundationModels` - List all available foundation models in each region
- `bedrock:GetInferenceProfile` - Check for global inference profile availability
- `ec2:DescribeRegions` - Discover all AWS regions to scan

### Workflows

- **publish.yml**: Runs weekly (or manually) to scan AWS Bedrock, update model IDs, and publish to PyPI if changes are detected
- **release.yml**: Triggered on version tags (e.g., `v0.2.0`) to create releases

### Manual Trigger

You can manually trigger the publish workflow:
1. Go to Actions tab in GitHub
2. Select "Generate Models and Publish to PyPI"
3. Click "Run workflow"

## License

MIT-0

## Author

Massimiliano Angelino <massi.ang@gmail.com>
