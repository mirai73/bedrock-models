import { crisModelId, globalModelId } from "./utils";

/**
 * Specialized string type that adds Bedrock-specific methods.
 */
export class BedrockModel extends String {
  constructor(value: string) {
    super(value);
  }

  /**
   * Get the cross-region inference (CRIS) model ID for this model.
   */
  cris(region: string): string {
    return crisModelId(this.toString(), region);
  }

  /**
   * Get the global inference profile ID for this model.
   */
  global(region: string): string {
    return globalModelId(this.toString(), region);
  }
}

export const Models = {
  AMAZON_NOVA_2_LITE: new BedrockModel('amazon.nova-2-lite-v1:0'),
  AMAZON_NOVA_LITE: new BedrockModel('amazon.nova-lite-v1:0'),
  AMAZON_NOVA_MICRO: new BedrockModel('amazon.nova-micro-v1:0'),
  AMAZON_NOVA_PRO: new BedrockModel('amazon.nova-pro-v1:0'),
  ANTHROPIC_CLAUDE_HAIKU_4_5_20251001: new BedrockModel('anthropic.claude-haiku-4-5-20251001-v1:0'),
  ANTHROPIC_CLAUDE_OPUS_4_5_20251101: new BedrockModel('anthropic.claude-opus-4-5-20251101-v1:0'),
  ANTHROPIC_CLAUDE_OPUS_4_6: new BedrockModel('anthropic.claude-opus-4-6-v1'),
  ANTHROPIC_CLAUDE_SONNET_4_20250514: new BedrockModel('anthropic.claude-sonnet-4-20250514-v1:0'),
  ANTHROPIC_CLAUDE_SONNET_4_5_20250929: new BedrockModel('anthropic.claude-sonnet-4-5-20250929-v1:0'),
  ANTHROPIC_CLAUDE_SONNET_4_6: new BedrockModel('anthropic.claude-sonnet-4-6'),
  TWELVELABS_PEGASUS_1_2: new BedrockModel('twelvelabs.pegasus-1-2-v1:0'),
};
