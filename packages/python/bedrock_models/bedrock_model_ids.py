"""
Auto-generated class containing AWS Bedrock Foundation Model IDs.
"""

import warnings
from .utils import cris_model_id, global_model_id


class BedrockModel(str):
    """Specialized string type that adds Bedrock-specific methods."""

    def cris(self, region: str = None) -> str:
        """Get the cross-region inference (CRIS) model ID for this model."""
        return cris_model_id(str(self), region)

    def global_cris(self, region: str = None) -> str:
        """Get the global inference profile ID for this model."""
        return global_model_id(str(self), region)


class _DeprecatedModelDescriptor:
    """Descriptor that emits deprecation warning when accessed."""
    def __init__(self, model_id: str, message: str):
        self.model_id = BedrockModel(model_id)
        self.message = message
    def __get__(self, obj, objtype=None):
        warnings.warn(self.message, DeprecationWarning, stacklevel=2)
        return self.model_id
    def __set_name__(self, owner, name):
        self.name = name


class Models:
    """Static class containing Bedrock foundation model IDs as constants."""

    AMAZON_NOVA_2_LITE = BedrockModel("amazon.nova-2-lite-v1:0")
    AMAZON_NOVA_LITE = BedrockModel("amazon.nova-lite-v1:0")
    AMAZON_NOVA_MICRO = BedrockModel("amazon.nova-micro-v1:0")
    AMAZON_NOVA_PRO = BedrockModel("amazon.nova-pro-v1:0")
    ANTHROPIC_CLAUDE_HAIKU_4_5_20251001 = BedrockModel("anthropic.claude-haiku-4-5-20251001-v1:0")
    ANTHROPIC_CLAUDE_OPUS_4_5_20251101 = BedrockModel("anthropic.claude-opus-4-5-20251101-v1:0")
    ANTHROPIC_CLAUDE_OPUS_4_6 = BedrockModel("anthropic.claude-opus-4-6-v1")
    ANTHROPIC_CLAUDE_SONNET_4_20250514 = BedrockModel("anthropic.claude-sonnet-4-20250514-v1:0")
    ANTHROPIC_CLAUDE_SONNET_4_5_20250929 = BedrockModel("anthropic.claude-sonnet-4-5-20250929-v1:0")
    ANTHROPIC_CLAUDE_SONNET_4_6 = BedrockModel("anthropic.claude-sonnet-4-6")
    TWELVELABS_PEGASUS_1_2 = BedrockModel("twelvelabs.pegasus-1-2-v1:0")
