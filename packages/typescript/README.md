# Bedrock Models (TypeScript)

A TypeScript library that provides AWS Bedrock Foundation Model IDs with autocomplete support and utility functions for cross-region inference.

## Features

- **Type-safe model IDs**: Access all Bedrock model IDs as constants with full autocomplete support.
- **Cross-Region Inference (CRIS)**: Automatically generate geo-prefixed or global model IDs.
- **Region Validation**: Check model availability across AWS regions.
- **Fluent API**: Use methods directly on model IDs for a cleaner developer experience.

## Installation

```bash
npm install bedrock-models
```

## Quick Start

```typescript
import { Models, crisModelId, globalModelId } from 'bedrock-models';

// 1. Basic Model IDs
const model = Models.ANTHROPIC_CLAUDE_SONNET_4_5_20250929;
// Returns: "anthropic.claude-sonnet-4-5-20250929-v1:0"

// 2. Cross-Region Inference (CRIS)
// Automatically chooses geo or global based on availability
const crisId = crisModelId(model, 'us-east-1');
// Returns: "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

// 3. Fluent API (Recommended)
const fluentId = Models.AMAZON_NOVA_PRO.cris('us-west-2');
// Returns: "us.amazon.nova-pro-v1:0"

const globalId = Models.AMAZON_NOVA_PRO.global('us-east-1');
// Returns: "global.amazon.nova-pro-v1:0"

// Qwen example
const qwenId = Models.QWEN_QWEN3_32B.cris('ap-southeast-1');
// Returns: "apac.qwen.qwen3-32b-v1:0"
```

## Usage

### Check Model Availability

```typescript
import { isModelAvailable, getAvailableRegions, Models } from 'bedrock-models';

// Check if a model is available in a specific region
const available = isModelAvailable(Models.AMAZON_NOVA_PRO, 'us-west-2');
// Returns: true or false

// Get all regions where a model is available
const regions = getAvailableRegions(Models.ANTHROPIC_CLAUDE_SONNET_4_5_20250929);
// Returns: ['us-east-1', 'us-west-2', 'ap-south-1', ...]
```

### Inference Profiles

```typescript
import { Models, hasGlobalProfile } from 'bedrock-models';

// Check if a model has a global inference profile in a region
const hasGlobal = hasGlobalProfile(
  Models.ANTHROPIC_CLAUDE_SONNET_4_5_20250929,
  'us-east-1'
);
// Returns: true or false
```

## Development

### Setup

```bash
pnpm install
pnpm build
```

### Running Tests

```bash
pnpm test
```

## License

MIT
