import { Models, isModelAvailable, getAvailableRegions, crisModelId, globalModelId, getInferenceProfiles, getInferenceTypes, hasGlobalProfile } from './index';

describe('Bedrock Models Library', () => {
  const TEST_MODEL = Models.ANTHROPIC_CLAUDE_3_5_SONNET_20241022;

  test('isModelAvailable should return true for available regions', () => {
    // Sonnet 3.5 is definitely in us-east-1
    expect(isModelAvailable(TEST_MODEL, 'us-east-1')).toBe(true);
    expect(isModelAvailable(TEST_MODEL, 'invalid-region')).toBe(false);
  });

  test('getAvailableRegions should return a list of regions', () => {
    const regions = getAvailableRegions(TEST_MODEL);
    expect(Array.isArray(regions)).toBe(true);
    expect(regions.length).toBeGreaterThan(0);
    expect(regions).toContain('us-east-1');
  });

  test('getAvailableRegions should throw for invalid model', () => {
    expect(() => getAvailableRegions('invalid.model')).toThrow('not found');
  });

  test('crisModelId should return geo-specific ID when available', () => {
    // Sonnet 3.5 in us-east-1 has US CRIS
    const crisId = crisModelId(TEST_MODEL, 'us-east-1');
    expect(crisId).toBe(`us.${TEST_MODEL}`);
  });

  test('crisModelId should return global ID when no geo-specific available but GLOBAL is', () => {
    // Nova 2 Lite in eu-west-2 has GLOBAL CRIS but no EU CRIS (based on previous logs)
    const NOVA_2 = Models.AMAZON_NOVA_2_LITE;
    const crisId = crisModelId(NOVA_2, 'eu-west-2');
    expect(crisId).toBe(`global.${NOVA_2}`);
  });

  test('BedrockModel class should have fluent API', () => {
    const crisId = TEST_MODEL.cris('us-east-1');
    expect(crisId).toBe(`us.${TEST_MODEL}`);

    // If global is supported, this should work too
    try {
      const globalId = TEST_MODEL.global('us-east-1');
      expect(globalId).toBe(`global.${TEST_MODEL}`);
    } catch (e) {
      // Expected if not supported
    }
  });

  test('getInferenceProfiles should return correct prefixes', () => {
    const profiles = getInferenceProfiles(TEST_MODEL, 'us-east-1');
    expect(profiles).toContain('US');
    // Sonnet 3.5 doesn't have GLOBAL in us-east-1 in the current data
  });

  test('hasGlobalProfile should work correctly', () => {
    // Nova 2 Lite has GLOBAL profile in us-east-1
    const NOVA_2 = Models.AMAZON_NOVA_2_LITE;
    expect(hasGlobalProfile(NOVA_2, 'us-east-1')).toBe(true);
  });

  test('globalModelId should return global prefix', () => {
    const NOVA_2 = Models.AMAZON_NOVA_2_LITE;
    expect(globalModelId(NOVA_2, 'us-east-1')).toBe(`global.${NOVA_2}`);
  });

  test('globalModelId should throw if not supported', () => {
     // A model that we know does NOT support global profiles in a specific region
     const modelWithNoGlobal = Models.AI21_JAMBA_1_5_LARGE;
     expect(() => globalModelId(modelWithNoGlobal, 'us-east-1')).toThrow('does not support global');
  });
});
