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

    AI21_JAMBA_1_5_LARGE = BedrockModel("ai21.jamba-1-5-large-v1:0")
    AI21_JAMBA_1_5_MINI = BedrockModel("ai21.jamba-1-5-mini-v1:0")
    AMAZON_NOVA_2_LITE = BedrockModel("amazon.nova-2-lite-v1:0")
    AMAZON_NOVA_2_MULTIMODAL_EMBEDDINGS = BedrockModel("amazon.nova-2-multimodal-embeddings-v1:0")
    AMAZON_NOVA_2_SONIC = BedrockModel("amazon.nova-2-sonic-v1:0")
    AMAZON_NOVA_CANVAS = BedrockModel("amazon.nova-canvas-v1:0")
    AMAZON_NOVA_LITE = BedrockModel("amazon.nova-lite-v1:0")
    AMAZON_NOVA_MICRO = BedrockModel("amazon.nova-micro-v1:0")
    AMAZON_NOVA_PREMIER = BedrockModel("amazon.nova-premier-v1:0")
    AMAZON_NOVA_PRO = BedrockModel("amazon.nova-pro-v1:0")
    AMAZON_NOVA_REEL = BedrockModel("amazon.nova-reel-v1:1")
    AMAZON_NOVA_SONIC = BedrockModel("amazon.nova-sonic-v1:0")
    AMAZON_RERANK = BedrockModel("amazon.rerank-v1:0")
    AMAZON_TITAN_EMBED_G1_TEXT_02 = BedrockModel("amazon.titan-embed-g1-text-02")
    AMAZON_TITAN_EMBED_IMAGE = BedrockModel("amazon.titan-embed-image-v1")
    AMAZON_TITAN_EMBED_TEXT = BedrockModel("amazon.titan-embed-text-v2:0")
    AMAZON_TITAN_IMAGE_GENERATOR = BedrockModel("amazon.titan-image-generator-v2:0")
    AMAZON_TITAN_TG1_LARGE = BedrockModel("amazon.titan-tg1-large")
    ANTHROPIC_CLAUDE_3_5_HAIKU_20241022 = BedrockModel("anthropic.claude-3-5-haiku-20241022-v1:0")
    ANTHROPIC_CLAUDE_3_HAIKU_20240307 = BedrockModel("anthropic.claude-3-haiku-20240307-v1:0")
    ANTHROPIC_CLAUDE_HAIKU_4_5_20251001 = BedrockModel("anthropic.claude-haiku-4-5-20251001-v1:0")
    ANTHROPIC_CLAUDE_OPUS_4_1_20250805 = BedrockModel("anthropic.claude-opus-4-1-20250805-v1:0")
    ANTHROPIC_CLAUDE_OPUS_4_5_20251101 = BedrockModel("anthropic.claude-opus-4-5-20251101-v1:0")
    ANTHROPIC_CLAUDE_OPUS_4_6 = BedrockModel("anthropic.claude-opus-4-6-v1")
    ANTHROPIC_CLAUDE_SONNET_4_20250514 = BedrockModel("anthropic.claude-sonnet-4-20250514-v1:0")
    ANTHROPIC_CLAUDE_SONNET_4_5_20250929 = BedrockModel("anthropic.claude-sonnet-4-5-20250929-v1:0")
    COHERE_COMMAND_R = BedrockModel("cohere.command-r-v1:0")
    COHERE_COMMAND_R_PLUS = BedrockModel("cohere.command-r-plus-v1:0")
    COHERE_EMBED = BedrockModel("cohere.embed-v4:0")
    COHERE_EMBED_ENGLISH = BedrockModel("cohere.embed-english-v3")
    COHERE_EMBED_MULTILINGUAL = BedrockModel("cohere.embed-multilingual-v3")
    COHERE_RERANK = BedrockModel("cohere.rerank-v3-5:0")
    DEEPSEEK_R1 = BedrockModel("deepseek.r1-v1:0")
    DEEPSEEK_V3 = BedrockModel("deepseek.v3-v1:0")
    DEEPSEEK_V3_2 = BedrockModel("deepseek.v3.2")
    GOOGLE_GEMMA_3_12B_IT = BedrockModel("google.gemma-3-12b-it")
    GOOGLE_GEMMA_3_27B_IT = BedrockModel("google.gemma-3-27b-it")
    GOOGLE_GEMMA_3_4B_IT = BedrockModel("google.gemma-3-4b-it")
    LUMA_RAY = BedrockModel("luma.ray-v2:0")
    META_LLAMA3_1_405B_INSTRUCT = BedrockModel("meta.llama3-1-405b-instruct-v1:0")
    META_LLAMA3_1_70B_INSTRUCT = BedrockModel("meta.llama3-1-70b-instruct-v1:0")
    META_LLAMA3_1_8B_INSTRUCT = BedrockModel("meta.llama3-1-8b-instruct-v1:0")
    META_LLAMA3_2_11B_INSTRUCT = BedrockModel("meta.llama3-2-11b-instruct-v1:0")
    META_LLAMA3_2_1B_INSTRUCT = BedrockModel("meta.llama3-2-1b-instruct-v1:0")
    META_LLAMA3_2_3B_INSTRUCT = BedrockModel("meta.llama3-2-3b-instruct-v1:0")
    META_LLAMA3_2_90B_INSTRUCT = BedrockModel("meta.llama3-2-90b-instruct-v1:0")
    META_LLAMA3_3_70B_INSTRUCT = BedrockModel("meta.llama3-3-70b-instruct-v1:0")
    META_LLAMA3_70B_INSTRUCT = BedrockModel("meta.llama3-70b-instruct-v1:0")
    META_LLAMA3_8B_INSTRUCT = BedrockModel("meta.llama3-8b-instruct-v1:0")
    META_LLAMA4_MAVERICK_17B_INSTRUCT = BedrockModel("meta.llama4-maverick-17b-instruct-v1:0")
    META_LLAMA4_SCOUT_17B_INSTRUCT = BedrockModel("meta.llama4-scout-17b-instruct-v1:0")
    MINIMAX_MINIMAX_M2 = BedrockModel("minimax.minimax-m2")
    MINIMAX_MINIMAX_M2_1 = BedrockModel("minimax.minimax-m2.1")
    MISTRAL_MAGISTRAL_SMALL_2509 = BedrockModel("mistral.magistral-small-2509")
    MISTRAL_MINISTRAL_3_14B_INSTRUCT = BedrockModel("mistral.ministral-3-14b-instruct")
    MISTRAL_MINISTRAL_3_3B_INSTRUCT = BedrockModel("mistral.ministral-3-3b-instruct")
    MISTRAL_MINISTRAL_3_8B_INSTRUCT = BedrockModel("mistral.ministral-3-8b-instruct")
    MISTRAL_MISTRAL_7B_INSTRUCT = BedrockModel("mistral.mistral-7b-instruct-v0:2")
    MISTRAL_MISTRAL_LARGE_2402 = BedrockModel("mistral.mistral-large-2402-v1:0")
    MISTRAL_MISTRAL_LARGE_2407 = BedrockModel("mistral.mistral-large-2407-v1:0")
    MISTRAL_MISTRAL_LARGE_3_675B_INSTRUCT = BedrockModel("mistral.mistral-large-3-675b-instruct")
    MISTRAL_MISTRAL_SMALL_2402 = BedrockModel("mistral.mistral-small-2402-v1:0")
    MISTRAL_MIXTRAL_8X7B_INSTRUCT = BedrockModel("mistral.mixtral-8x7b-instruct-v0:1")
    MISTRAL_PIXTRAL_LARGE_2502 = BedrockModel("mistral.pixtral-large-2502-v1:0")
    MISTRAL_VOXTRAL_MINI_3B_2507 = BedrockModel("mistral.voxtral-mini-3b-2507")
    MISTRAL_VOXTRAL_SMALL_24B_2507 = BedrockModel("mistral.voxtral-small-24b-2507")
    MOONSHOTAI_KIMI_K2_5 = BedrockModel("moonshotai.kimi-k2.5")
    MOONSHOT_KIMI_K2_THINKING = BedrockModel("moonshot.kimi-k2-thinking")
    NVIDIA_NEMOTRON_NANO_12B = BedrockModel("nvidia.nemotron-nano-12b-v2")
    NVIDIA_NEMOTRON_NANO_3_30B = BedrockModel("nvidia.nemotron-nano-3-30b")
    NVIDIA_NEMOTRON_NANO_9B = BedrockModel("nvidia.nemotron-nano-9b-v2")
    OPENAI_GPT_OSS_120B = BedrockModel("openai.gpt-oss-120b-1:0")
    OPENAI_GPT_OSS_20B = BedrockModel("openai.gpt-oss-20b-1:0")
    OPENAI_GPT_OSS_SAFEGUARD_120B = BedrockModel("openai.gpt-oss-safeguard-120b")
    OPENAI_GPT_OSS_SAFEGUARD_20B = BedrockModel("openai.gpt-oss-safeguard-20b")
    QWEN_QWEN3_235B_A22B_2507 = BedrockModel("qwen.qwen3-235b-a22b-2507-v1:0")
    QWEN_QWEN3_32B = BedrockModel("qwen.qwen3-32b-v1:0")
    QWEN_QWEN3_CODER_30B_A3B = BedrockModel("qwen.qwen3-coder-30b-a3b-v1:0")
    QWEN_QWEN3_CODER_480B_A35B = BedrockModel("qwen.qwen3-coder-480b-a35b-v1:0")
    QWEN_QWEN3_CODER_NEXT = BedrockModel("qwen.qwen3-coder-next")
    QWEN_QWEN3_NEXT_80B_A3B = BedrockModel("qwen.qwen3-next-80b-a3b")
    QWEN_QWEN3_VL_235B_A22B = BedrockModel("qwen.qwen3-vl-235b-a22b")
    STABILITY_SD3_5_LARGE = BedrockModel("stability.sd3-5-large-v1:0")
    STABILITY_STABLE_CONSERVATIVE_UPSCALE = BedrockModel("stability.stable-conservative-upscale-v1:0")
    STABILITY_STABLE_CREATIVE_UPSCALE = BedrockModel("stability.stable-creative-upscale-v1:0")
    STABILITY_STABLE_FAST_UPSCALE = BedrockModel("stability.stable-fast-upscale-v1:0")
    STABILITY_STABLE_IMAGE_CONTROL_SKETCH = BedrockModel("stability.stable-image-control-sketch-v1:0")
    STABILITY_STABLE_IMAGE_CONTROL_STRUCTURE = BedrockModel("stability.stable-image-control-structure-v1:0")
    STABILITY_STABLE_IMAGE_CORE = BedrockModel("stability.stable-image-core-v1:1")
    STABILITY_STABLE_IMAGE_ERASE_OBJECT = BedrockModel("stability.stable-image-erase-object-v1:0")
    STABILITY_STABLE_IMAGE_INPAINT = BedrockModel("stability.stable-image-inpaint-v1:0")
    STABILITY_STABLE_IMAGE_REMOVE_BACKGROUND = BedrockModel("stability.stable-image-remove-background-v1:0")
    STABILITY_STABLE_IMAGE_SEARCH_RECOLOR = BedrockModel("stability.stable-image-search-recolor-v1:0")
    STABILITY_STABLE_IMAGE_SEARCH_REPLACE = BedrockModel("stability.stable-image-search-replace-v1:0")
    STABILITY_STABLE_IMAGE_STYLE_GUIDE = BedrockModel("stability.stable-image-style-guide-v1:0")
    STABILITY_STABLE_IMAGE_ULTRA = BedrockModel("stability.stable-image-ultra-v1:1")
    STABILITY_STABLE_OUTPAINT = BedrockModel("stability.stable-outpaint-v1:0")
    STABILITY_STABLE_STYLE_TRANSFER = BedrockModel("stability.stable-style-transfer-v1:0")
    TWELVELABS_MARENGO_EMBED_2_7 = BedrockModel("twelvelabs.marengo-embed-2-7-v1:0")
    TWELVELABS_MARENGO_EMBED_3_0 = BedrockModel("twelvelabs.marengo-embed-3-0-v1:0")
    TWELVELABS_PEGASUS_1_2 = BedrockModel("twelvelabs.pegasus-1-2-v1:0")
    WRITER_PALMYRA_X4 = BedrockModel("writer.palmyra-x4-v1:0")
    WRITER_PALMYRA_X5 = BedrockModel("writer.palmyra-x5-v1:0")
    ZAI_GLM_4_7 = BedrockModel("zai.glm-4.7")
    ZAI_GLM_4_7_FLASH = BedrockModel("zai.glm-4.7-flash")
    ANTHROPIC_CLAUDE_3_5_SONNET_20240620 = _DeprecatedModelDescriptor("anthropic.claude-3-5-sonnet-20240620-v1:0", "Model 'anthropic.claude-3-5-sonnet-20240620-v1:0' has LEGACY status and may be removed by AWS. Consider migrating to a newer model.")
    ANTHROPIC_CLAUDE_3_5_SONNET_20241022 = _DeprecatedModelDescriptor("anthropic.claude-3-5-sonnet-20241022-v2:0", "Model 'anthropic.claude-3-5-sonnet-20241022-v2:0' has LEGACY status and may be removed by AWS. Consider migrating to a newer model.")
    ANTHROPIC_CLAUDE_3_7_SONNET_20250219 = _DeprecatedModelDescriptor("anthropic.claude-3-7-sonnet-20250219-v1:0", "Model 'anthropic.claude-3-7-sonnet-20250219-v1:0' has LEGACY status and may be removed by AWS. Consider migrating to a newer model.")
    ANTHROPIC_CLAUDE_3_OPUS_20240229 = _DeprecatedModelDescriptor("anthropic.claude-3-opus-20240229-v1:0", "Model 'anthropic.claude-3-opus-20240229-v1:0' has LEGACY status and may be removed by AWS. Consider migrating to a newer model.")
    ANTHROPIC_CLAUDE_3_SONNET_20240229 = _DeprecatedModelDescriptor("anthropic.claude-3-sonnet-20240229-v1:0", "Model 'anthropic.claude-3-sonnet-20240229-v1:0' has LEGACY status and may be removed by AWS. Consider migrating to a newer model.")
    ANTHROPIC_CLAUDE_OPUS_4_20250514 = _DeprecatedModelDescriptor("anthropic.claude-opus-4-20250514-v1:0", "Model 'anthropic.claude-opus-4-20250514-v1:0' has LEGACY status and may be removed by AWS. Consider migrating to a newer model.")
