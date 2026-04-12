"""Tests for the Python fluent API."""

import pytest
import warnings
from bedrock_models import Models
from bedrock_models.utils import load_model_data
from bedrock_models.bedrock_model_ids import _DeprecatedModelDescriptor

def get_dynamic_model(condition):
    """
    Find a model constant and a region that satisfies the given condition.
    Returns (model_id_str, attribute_value, region, data) or (None, None, None, None)
    """
    model_data = load_model_data()
    for name, attr in vars(Models).items():
        if name.startswith("_") or name == "m":
            continue
            
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                model = getattr(Models, name)
            except Exception:
                continue
                
        if not isinstance(model, str):
            continue
            
        m_id = str(model)
        if m_id not in model_data:
            continue
            
        data = model_data[m_id]
        is_legacy = isinstance(attr, _DeprecatedModelDescriptor)
        for region in data.get("regions", []):
            if condition(m_id, data, region, is_legacy):
                return m_id, model, region, data
                
    return None, None, None, None


def test_fluent_cris():
    """Test the .cris() method on model constants."""
    def condition(m_id, data, region, is_legacy):
        if is_legacy:
            return False
        inference_types = data.get("inference_types", {}).get(region, [])
        geo_profiles = [t for t in inference_types if t not in ("ON_DEMAND", "GLOBAL", "PROVISIONED")]
        return len(geo_profiles) > 0

    m_id, model, region, data = get_dynamic_model(condition)
    if not model:
        pytest.skip("No non-legacy model found with geo-CRIS support.")
        
    inference_types = data.get("inference_types", {}).get(region, [])
    geo_profiles = [t for t in inference_types if t not in ("ON_DEMAND", "GLOBAL", "PROVISIONED")]
    expected_prefix = geo_profiles[0].lower()
    
    # Should work via method call
    cris_id = model.cris(region)
    assert cris_id == f"{expected_prefix}.{model}"
    
    # Still behaves like a string
    assert isinstance(model, str)
    assert model == m_id

def test_fluent_global_cris():
    """Test the .global_cris() method on model constants."""
    def condition(m_id, data, region, is_legacy):
        if is_legacy:
            return False
        inference_types = data.get("inference_types", {}).get(region, [])
        return "GLOBAL" in inference_types

    m_id, model, region, data = get_dynamic_model(condition)
    if not model:
        pytest.skip("No non-legacy model found with GLOBAL inference profile.")
        
    global_id = model.global_cris(region)
    assert global_id == f"global.{model}"

def test_legacy_model_fluent():
    """Test that legacy models (descriptors) also support fluent API."""
    def condition(m_id, data, region, is_legacy):
        if not is_legacy:
            return False
        inference_types = data.get("inference_types", {}).get(region, [])
        geo_profiles = [t for t in inference_types if t not in ("ON_DEMAND", "GLOBAL", "PROVISIONED")]
        return len(geo_profiles) > 0
        
    m_id, model, region, data = get_dynamic_model(condition)
    if not model:
        pytest.skip("No legacy model found with geo-CRIS support.")

    attr_name = None
    for name, attr in vars(Models).items():
        if isinstance(attr, _DeprecatedModelDescriptor) and attr.model_id == m_id:
            attr_name = name
            break
            
    with pytest.warns(DeprecationWarning):
        legacy_model = getattr(Models, attr_name)
        cris_id = legacy_model.cris(region)
        
        inference_types = data.get("inference_types", {}).get(region, [])
        geo_profiles = [t for t in inference_types if t not in ("ON_DEMAND", "GLOBAL", "PROVISIONED")]
        expected_prefix = geo_profiles[0].lower()
        
        assert cris_id == f"{expected_prefix}.{legacy_model}"

def test_fluent_api_invalid_region():
    """Test fluent API with invalid region."""
    def condition(m_id, data, region, is_legacy):
        return True 
        
    m_id, model, region, data = get_dynamic_model(condition)
    if not model:
        pytest.skip("No model found to test invalid region.")
        
    invalid_region = "invalid-region"
    
    with pytest.raises(ValueError, match="not available in region"):
        model.cris(invalid_region)
