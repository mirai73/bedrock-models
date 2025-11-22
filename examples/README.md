# Bedrock Models Examples

This directory contains example scripts demonstrating how to use the bedrock-models library.

## Examples

### [quickstart.py](quickstart.py)
A minimal example showing the basic functionality:
- Accessing model IDs
- Checking availability
- Getting cross-region inference IDs

Run it:
```bash
python examples/quickstart.py
```

### [usage_example.py](usage_example.py)
A comprehensive example covering all features:
- Basic model ID access
- Cross-region inference (CRIS) for US, EU, and APAC
- Checking model availability across regions
- Working with global inference profiles
- Practical use case: selecting the best endpoint
- Integration with boto3

Run it:
```bash
python examples/usage_example.py
```

## Installation

Make sure you have the package installed:
```bash
pip install bedrock-models
```

Or if you're developing locally:
```bash
poetry install
poetry run python examples/usage_example.py
```
