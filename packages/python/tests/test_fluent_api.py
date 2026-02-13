"""Tests for the Python fluent API."""

import pytest
from bedrock_models import Models

def test_fluent_cris():
    """Test the .cris() method on model constants."""
    model = Models.ANTHROPIC_CLAUDE_3_5_SONNET_20241022
    region = "us-east-1"
    
    # Should work via method call
    cris_id = model.cris(region)
    assert cris_id == f"us.{model}"
    
    # Still behaves like a string
    assert isinstance(model, str)
    assert model == "anthropic.claude-3-5-sonnet-20241022-v2:0"

def test_fluent_global_cris():
    """Test the .global_cris() method on model constants."""
    # Nova 2 Lite supports global CRIS in us-east-1
    model = Models.AMAZON_NOVA_2_LITE
    region = "us-east-1"
    
    global_id = model.global_cris(region)
    assert global_id == f"global.{model}"

def test_legacy_model_fluent():
    """Test that legacy models (descriptors) also support fluent API."""
    region = "us-east-1"
    
    with pytest.warns(DeprecationWarning):
        # Accessing the attribute emits the warning
        model = Models.ANTHROPIC_CLAUDE_3_5_SONNET_20240620
        cris_id = model.cris(region)
        assert cris_id == f"us.{model}"

def test_fluent_api_invalid_region():
    """Test fluent API with invalid region."""
    model = Models.AMAZON_NOVA_LITE
    
    with pytest.raises(ValueError, match="not available in region"):
        model.cris("invalid-region")
