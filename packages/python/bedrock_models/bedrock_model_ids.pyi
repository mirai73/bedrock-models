from typing import Final, Optional

class BedrockModel(str):
    def cris(self, region: Optional[str] = None) -> str: ...
    def global_cris(self, region: Optional[str] = None) -> str: ...

class Models:

    AMAZON_NOVA_2_LITE: Final[BedrockModel]
    AMAZON_NOVA_LITE: Final[BedrockModel]
    AMAZON_NOVA_MICRO: Final[BedrockModel]
    AMAZON_NOVA_PRO: Final[BedrockModel]
    ANTHROPIC_CLAUDE_HAIKU_4_5_20251001: Final[BedrockModel]
    ANTHROPIC_CLAUDE_OPUS_4_5_20251101: Final[BedrockModel]
    ANTHROPIC_CLAUDE_OPUS_4_6: Final[BedrockModel]
    ANTHROPIC_CLAUDE_SONNET_4_20250514: Final[BedrockModel]
    ANTHROPIC_CLAUDE_SONNET_4_5_20250929: Final[BedrockModel]
    ANTHROPIC_CLAUDE_SONNET_4_6: Final[BedrockModel]
    TWELVELABS_PEGASUS_1_2: Final[BedrockModel]
