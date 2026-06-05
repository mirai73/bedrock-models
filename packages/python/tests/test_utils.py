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
    assert result.startswith("us.")
    assert model_id in result

def test_cris_model_id_on_demand():
    """Test getting CRIS model ID (geo or global)."""
    from bedrock_models import cris_model_id
    
    model_id = Models.AMAZON_NOVA_LITE
    
    # Test with explicit region
    result = cris_model_id(model_id, region="us-east-1")
    # Should return geo CRIS if INFERENCE_PROFILE is available
    assert result.startswith("us.")
    assert model_id in result

def test_cris_model_id_global():
    """Test getting CRIS model ID (geo or global)."""
    from bedrock_models import cris_model_id
    
    model_id = Models.AMAZON_NOVA_2_LITE
    
    # Test with explicit region
    result = cris_model_id(model_id, region="eu-west-2")
    # Should return geo CRIS if INFERENCE_PROFILE is available
    assert result.startswith("global.")
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


def test_save_to_json_metadata(tmp_path):
    """Test save_to_json updates bedrock_models_metadata.json correctly."""
    import sys
    import json
    from pathlib import Path
    from datetime import datetime, timezone
    
    # Add utils path to sys.path
    utils_dir = str(Path(__file__).parent.parent / "utils")
    if utils_dir not in sys.path:
        sys.path.append(utils_dir)
        
    from generate_models_json import save_to_json
    
    models_file = tmp_path / "bedrock_models.json"
    metadata_file = tmp_path / "bedrock_models_metadata.json"
    
    # 1. Initial run: save new models
    initial_mapping = {
        "model-a": {
            "regions": ["us-east-1"],
            "inference_types": {"us-east-1": ["ON_DEMAND"]},
            "inputModalities": {"TEXT"},
            "outputModalities": {"TEXT"},
        },
        "model-b": {
            "regions": ["us-west-2"],
            "inference_types": {"us-west-2": ["ON_DEMAND"]},
            "inputModalities": {"TEXT"},
            "outputModalities": {"TEXT"},
        }
    }
    
    current_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    save_to_json(initial_mapping, filename=str(models_file))
    
    # Check that both files exist
    assert models_file.exists()
    assert metadata_file.exists()
    
    with open(metadata_file, "r") as f:
        meta_data = json.load(f)
        
    assert "model-a" in meta_data
    assert meta_data["model-a"]["last_changed"] == current_date
    assert "deleted" not in meta_data["model-a"]
    
    assert "model-b" in meta_data
    assert meta_data["model-b"]["last_changed"] == current_date
    assert "deleted" not in meta_data["model-b"]

    # 2. Modify one model, leave other unchanged
    # We will override the saved files with some historical metadata dates to test preservation
    historical_meta = {
        "model-a": {"last_changed": "2020-01-01"},
        "model-b": {"last_changed": "2020-01-01"}
    }
    with open(metadata_file, "w") as f:
        json.dump(historical_meta, f)
        
    # Run again with model-b modified and model-a unchanged
    modified_mapping = {
        "model-a": {
            "regions": ["us-east-1"],
            "inference_types": {"us-east-1": ["ON_DEMAND"]},
            "inputModalities": {"TEXT"},
            "outputModalities": {"TEXT"},
        },
        "model-b": {
            "regions": ["us-west-2", "us-east-1"], # Changed regions list
            "inference_types": {"us-west-2": ["ON_DEMAND"], "us-east-1": ["ON_DEMAND"]},
            "inputModalities": {"TEXT"},
            "outputModalities": {"TEXT"},
        }
    }
    save_to_json(modified_mapping, filename=str(models_file))
    
    with open(metadata_file, "r") as f:
        meta_data = json.load(f)
        
    # model-a unchanged -> retains historical date
    assert meta_data["model-a"]["last_changed"] == "2020-01-01"
    assert "deleted" not in meta_data["model-a"]
    
    # model-b changed -> updated to current date
    assert meta_data["model-b"]["last_changed"] == current_date
    assert "deleted" not in meta_data["model-b"]

    # 3. Delete a model (model-b)
    # Clear model-b from mapping
    deleted_mapping = {
        "model-a": {
            "regions": ["us-east-1"],
            "inference_types": {"us-east-1": ["ON_DEMAND"]},
            "inputModalities": {"TEXT"},
            "outputModalities": {"TEXT"},
        }
    }
    save_to_json(deleted_mapping, filename=str(models_file))
    
    with open(metadata_file, "r") as f:
        meta_data = json.load(f)
        
    # model-a unchanged
    assert meta_data["model-a"]["last_changed"] == "2020-01-01"
    
    # model-b deleted -> retained in metadata and marked deleted
    assert "model-b" in meta_data
    assert meta_data["model-b"]["last_changed"] == current_date # it changed in step 2
    assert meta_data["model-b"]["deleted"] == current_date
    
    # 4. Resurrect model-b
    save_to_json(modified_mapping, filename=str(models_file))
    with open(metadata_file, "r") as f:
        meta_data = json.load(f)
        
    # model-b resurrected -> 'deleted' is removed, 'last_changed' updated to current_date
    assert "deleted" not in meta_data["model-b"]
    assert meta_data["model-b"]["last_changed"] == current_date
