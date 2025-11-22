"""Tests for deprecation warnings on LEGACY models."""

import warnings
import pytest
from bedrock_models import Models


def test_legacy_model_shows_deprecation_warning():
    """Test that accessing a LEGACY model shows a deprecation warning."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Access a LEGACY model
        model_id = Models.AMAZON_TITAN_TEXT_EXPRESS
        
        # Check that a warning was issued
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "LEGACY status" in str(w[0].message)
        assert model_id == "amazon.titan-text-express-v1"


def test_active_model_no_deprecation_warning():
    """Test that accessing an ACTIVE model does not show a deprecation warning."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Access an ACTIVE model (Claude 3.7 Sonnet is newer and active)
        model_id = Models.ANTHROPIC_CLAUDE_3_7_SONNET_20250219
        
        # Check that no warning was issued
        assert len(w) == 0
        assert model_id == "anthropic.claude-3-7-sonnet-20250219-v1:0"


def test_multiple_legacy_model_accesses():
    """Test that each access to a LEGACY model shows a warning."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Access the same LEGACY model multiple times
        _ = Models.AMAZON_TITAN_TEXT_EXPRESS
        _ = Models.AMAZON_TITAN_TEXT_EXPRESS
        _ = Models.AMAZON_TITAN_TEXT_LITE
        
        # Each access should generate a warning
        assert len(w) == 3
        assert all(issubclass(warning.category, DeprecationWarning) for warning in w)
