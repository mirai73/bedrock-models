# Bedrock Models Explorer Monorepo

[![Build Status](https://github.com/mirai73/bedrock-models/actions/workflows/ci.yml/badge.svg)](https://github.com/mirai73/bedrock-models/actions)
[![License: MIT-0](https://img.shields.io/badge/License-MIT--0-blue.svg)](https://opensource.org/licenses/MIT-0)

A comprehensive toolkit for working with Amazon Bedrock foundation models, providing type-safe model IDs, cross-region inference utilities, and an interactive explorer.

## 🌐 [Browse Models Online](https://mirai73.github.io/bedrock-models/)

Explore all available Bedrock models with our interactive web interface. Search by model name, filter by region, and find CRIS-enabled models.

## Repository Structure

This is a monorepo managed with `pnpm` and `turbo`.

- **[`packages/python`](file:///packages/python)**: Python library with model constants and CRIS utilities.
- **[`packages/typescript`](file:///packages/typescript)**: TypeScript/JavaScript library with parity to the Python implementation.
- **[`apps/docs`](file:///apps/docs)**: Source for the interactive Model Explorer website.
- **[`packages/shared`](file:///packages/shared)**: Shared data (`bedrock_models.json`) and generation scripts.

## Features

- **Type-safe model IDs**: Access all Bedrock model IDs as constants with full autocomplete support in Python and TypeScript.
- **Cross-Region Inference (CRIS)**: Automatically generate geo-prefixed or global model IDs.
- **Region Validation**: Check model availability across AWS regions.
- **Auto-updated**: Model data is refreshed weekly from the AWS Bedrock API.

## Quick Start

### Python

```bash
pip install bedrock-models
```

```python
from bedrock_models import Models, cris_model_id

# Use model IDs with autocomplete
model_id = Models.ANTHROPIC_CLAUDE_SONNET_4_5_20250929
# Get regional CRIS ID
cris_id = cris_model_id(model_id, region="us-east-1")

# Qwen example
qwen_id = Models.QWEN_QWEN3_32B.cris("ap-southeast-1")
```

### TypeScript / JavaScript

```bash
npm install bedrock-models
```

```typescript
import { Models, crisModelId } from 'bedrock-models';

// Use model IDs with autocomplete
const modelId = Models.ANTHROPIC_CLAUDE_SONNET_4_5_20250929;
// Get regional CRIS ID
const crisId = crisModelId(modelId, 'us-east-1');

// Or use the fluent API
const fluentId = Models.ANTHROPIC_CLAUDE_SONNET_4_5_20250929.cris('us-east-1');

// Qwen example
const qwenId = Models.QWEN_QWEN3_32B.cris('ap-southeast-1');
```

## Development

### Prerequisites

- [pnpm](https://pnpm.io/)
- [Python 3.10+](https://www.python.org/)
- [Poetry](https://python-poetry.org/) (for Python package development)

### Setup

```bash
# Install Node.js dependencies
pnpm install

# Build all packages
pnpm build

# Run tests
pnpm test
```

### Regenerating Model Data

The model data is centralized in `packages/shared/bedrock_models.json`. To update it:

```bash
pnpm generate
```

This runs the Python script that fetches the latest models from AWS (requires AWS credentials).

## License

MIT-0
