import modelData from './bedrock_models.json';

export type ModelDataMap = {
  [modelId: string]: {
    regions: string[];
    inference_types: {
      [region: string]: string[];
    };
    model_lifecycle_status?: string;
  };
};

const data = modelData as ModelDataMap;

export function isModelAvailable(modelId: string | String, region: string): boolean {
  const id = modelId.toString();
  const model = data[id];
  if (!model) return false;
  return model.regions.includes(region);
}

export function getAvailableRegions(modelId: string | String): string[] {
  const id = modelId.toString();
  const model = data[id];
  if (!model) {
    throw new Error(`Model ID '${id}' not found in bedrock_models.json`);
  }
  return model.regions;
}

export function hasGlobalProfile(modelId: string | String, region: string): boolean {
  const id = modelId.toString();
  const model = data[id];
  if (!model) return false;
  const inferenceTypes = model.inference_types[region] || [];
  return inferenceTypes.includes('GLOBAL');
}

export function getInferenceProfiles(modelId: string | String, region: string): string[] {
  const id = modelId.toString();
  const model = data[id];
  if (!model) return [];
  const inferenceTypes = model.inference_types[region] || [];
  const profilePrefixes = ['US', 'EU', 'CA', 'JP', 'AU', 'APAC', 'AP', 'GLOBAL'];
  return inferenceTypes.filter(t => profilePrefixes.includes(t));
}

export function getInferenceTypes(modelId: string | String, region: string): string[] {
  const id = modelId.toString();
  const model = data[id];
  if (!model) return [];
  return model.inference_types[region] || [];
}

export function crisModelId(modelId: string | String, region: string): string {
  const id = modelId.toString();
  const model = data[id];
  if (!model) {
    throw new Error(`Model ID '${id}' not found in bedrock_models.json`);
  }

  if (!model.regions.includes(region)) {
    throw new Error(
      `Model '${id}' is not available in region '${region}'. Available regions: ${model.regions.join(', ')}`
    );
  }

  const inferenceTypes = model.inference_types[region] || [];

  // Check for geo-specific profile first
  const availableGeoProfiles = inferenceTypes.filter(t => t !== 'GLOBAL' && t !== 'ON_DEMAND' && t !== 'PROVISIONED');
  if (availableGeoProfiles.length > 0) {
    const prefix = availableGeoProfiles[0].toLowerCase();
    return `${prefix}.${id}`;
  }

  if (inferenceTypes.includes('GLOBAL')) {
    return `global.${id}`;
  }

  throw new Error(
    `Model '${id}' does not support CRIS in region '${region}'. Available inference types: ${inferenceTypes.join(', ')}`
  );
}

export function globalModelId(modelId: string | String, region: string): string {
  const id = modelId.toString();
  if (!hasGlobalProfile(id, region)) {
    const model = data[id];
    if (!model) {
      throw new Error(`Model ID '${id}' not found in bedrock_models.json`);
    }
    if (!model.regions.includes(region)) {
        throw new Error(
          `Model '${id}' is not available in region '${region}'. Available regions: ${model.regions.join(', ')}`
        );
    }
    const inferenceTypes = model.inference_types[region] || [];
    throw new Error(
      `Model '${id}' does not support global inference profile in region '${region}'. Available inference types: ${inferenceTypes.join(', ')}`
    );
  }
  return `global.${id}`;
}
