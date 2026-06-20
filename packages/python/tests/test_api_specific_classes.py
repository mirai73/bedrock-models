"""Tests for MantleModels and RuntimeModels classes."""

from bedrock_models import Models, MantleModels, RuntimeModels

def test_api_specific_classes_existence():
    # Verify that some known models exist and are bedrock model instances
    assert hasattr(MantleModels, "GOOGLE_GEMMA_3_12B_IT")
    assert isinstance(MantleModels.GOOGLE_GEMMA_3_12B_IT, str)
    assert MantleModels.GOOGLE_GEMMA_3_12B_IT == "google.gemma-3-12b-it"

    assert hasattr(RuntimeModels, "AMAZON_NOVA_2_LITE")
    assert isinstance(RuntimeModels.AMAZON_NOVA_2_LITE, str)
    assert RuntimeModels.AMAZON_NOVA_2_LITE == "amazon.nova-2-lite-v1:0"

def test_separation_logic():
    # AI21_JAMBA_1_5_LARGE is supported by runtime but not mantle
    assert hasattr(RuntimeModels, "AI21_JAMBA_1_5_LARGE")
    assert not hasattr(MantleModels, "AI21_JAMBA_1_5_LARGE")
