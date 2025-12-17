"""Tests for utility functions."""

import pytest
from bedrock_models import Models, is_model_available, get_available_regions


def test_is_model_available():
    """Test checking model availability in regions."""
    model_id = Models.ANTHROPIC_CLAUDE_SONNET_4_5_20250929
    # This should be available in us-east-1
    assert is_model_available(model_id, "us-east-1") or is_model_available(model_id, "us-west-2")


def test_is_model_available_invalid():
    """Test with invalid model."""
    assert not is_model_available("invalid.model", "us-east-1")


def test_is_model_available_without_region():
    """Test is_model_available without region (should use boto3)."""
    from unittest.mock import patch
    from bedrock_models import utils
    
    # Mock _get_region_from_boto3 to return None
    with patch.object(utils, '_get_region_from_boto3', return_value=None):
        with pytest.raises(ValueError, match="Region must be provided"):
            is_model_available(Models.ANTHROPIC_CLAUDE_SONNET_4_5_20250929)


def test_get_available_regions():
    """Test getting available regions for a model."""
    model_id = Models.ANTHROPIC_CLAUDE_SONNET_4_5_20250929
    regions = get_available_regions(model_id)
    assert isinstance(regions, list)
    assert len(regions) > 0


def test_get_available_regions_invalid():
    """Test getting regions for invalid model."""
    with pytest.raises(ValueError, match="not found"):
        get_available_regions("invalid.model-id")


def test_has_global_profile():
    """Test checking for global inference profile."""
    from bedrock_models import has_global_profile
    
    # Test with a model that might have global profile
    model_id = Models.ANTHROPIC_CLAUDE_SONNET_4_5_20250929
    regions = get_available_regions(model_id)
    
    # Just verify the function works without errors
    if regions:
        result = has_global_profile(model_id, regions[0])
        assert isinstance(result, bool)









def test_cris_model_id():
    """Test getting CRIS model ID (geo or global)."""
    from bedrock_models import cris_model_id
    
    model_id = Models.ANTHROPIC_CLAUDE_SONNET_4_5_20250929
    
    # Test with explicit region
    result = cris_model_id(model_id, region="us-east-1")
    # Should return geo CRIS if INFERENCE_PROFILE is available
    assert result.startswith("us.") or result.startswith("global.")
    assert model_id in result


def test_cris_model_id_without_region():
    """Test CRIS model ID without region (should use boto3)."""
    from bedrock_models import cris_model_id
    from unittest.mock import patch
    from bedrock_models import utils
    
    # Mock _get_region_from_boto3 to return None
    with patch.object(utils, '_get_region_from_boto3', return_value=None):
        with pytest.raises(ValueError, match="Region must be provided"):
            cris_model_id(Models.ANTHROPIC_CLAUDE_SONNET_4_5_20250929)


def test_global_model_id():
    """Test getting global model ID."""
    from bedrock_models import global_model_id
    
    model_id = Models.ANTHROPIC_CLAUDE_SONNET_4_5_20250929
    regions = get_available_regions(model_id)
    
    # Test with a region where the model is available
    if regions:
        region = regions[0]
        # This might fail if global profile is not available, which is expected
        try:
            result = global_model_id(model_id, region=region)
            assert result == f"global.{model_id}"
        except ValueError as e:
            # Expected if global profile is not supported
            assert "does not support global inference profile" in str(e)


def test_global_model_id_without_region():
    """Test global model ID without region (should use boto3)."""
    from bedrock_models import global_model_id
    from unittest.mock import patch
    from bedrock_models import utils
    
    # Mock _get_region_from_boto3 to return None
    with patch.object(utils, '_get_region_from_boto3', return_value=None):
        with pytest.raises(ValueError, match="Region must be provided"):
            global_model_id(Models.ANTHROPIC_CLAUDE_SONNET_4_5_20250929)


def test_ca_central_1_inference_profiles():
    """Test inference profiles in ca-central-1 region."""
    from bedrock_models import get_inference_profiles, get_inference_types, cris_model_id
    
    model_id = Models.ANTHROPIC_CLAUDE_SONNET_4_5_20250929
    region = "ca-central-1"
    
    # Check if model is available in ca-central-1
    if not is_model_available(model_id, region):
        pytest.skip(f"Model {model_id} not available in {region}")
    
    # Get inference profiles (should include US and GLOBAL)
    profiles = get_inference_profiles(model_id, region)
    assert "GLOBAL" in profiles, f"Expected GLOBAL profile in {region}"
    assert "US" in profiles, f"Expected US profile in {region}"
    
    # Get all inference types
    inference_types = get_inference_types(model_id, region)
    assert len(inference_types) > 0, f"Expected inference types in {region}"
    
    # CRIS should prefer US over GLOBAL
    cris_id = cris_model_id(model_id, region)
    assert cris_id.startswith("us."), f"Expected US profile to be preferred in {region}, got {cris_id}"
    assert model_id in cris_id


def test_me_central_1_inference_profiles():
    """Test inference profiles in me-central-1 region."""
    from bedrock_models import get_inference_profiles, get_inference_types, cris_model_id
    
    model_id = Models.ANTHROPIC_CLAUDE_SONNET_4_20250514
    region = "me-central-1"
    
    # Check if model is available in me-central-1
    if not is_model_available(model_id, region):
        pytest.skip(f"Model {model_id} not available in {region}")
    
    # Get inference profiles (should include APAC)
    profiles = get_inference_profiles(model_id, region)
    assert "APAC" in profiles, f"Expected APAC profile in {region}, got {profiles}"
    
    # Get all inference types
    inference_types = get_inference_types(model_id, region)
    assert len(inference_types) > 0, f"Expected inference types in {region}"
    
    # CRIS should use APAC profile
    cris_id = cris_model_id(model_id, region)
    assert cris_id.startswith("apac."), f"Expected APAC profile in {region}, got {cris_id}"
    assert model_id in cris_id
