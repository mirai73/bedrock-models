"""
Utility functions for working with Bedrock model IDs.
"""

import json
from pathlib import Path
from typing import Optional


def load_model_data() -> dict:
    """Load the bedrock_models.json data."""
    json_path = Path(__file__).parent / "bedrock_models.json"
    with open(json_path, "r") as f:
        return json.load(f)


def _get_region_from_boto3() -> Optional[str]:
    """
    Try to get the AWS region from boto3 session.
    
    Returns:
        The AWS region name if boto3 is available and configured, None otherwise
    """
    try:
        import boto3

        session = boto3.Session()
        return session.region_name
    except (ImportError, Exception):
        return None


def is_model_available(model_id: str, region: Optional[str] = None) -> bool:
    """
    Check if a model is available in a specific region.

    Args:
        model_id: The model ID to check
        region: The AWS region. If not provided, will attempt to get from boto3 session.

    Returns:
        True if the model is available in the region, False otherwise

    Raises:
        ValueError: If region cannot be determined (not provided and boto3 not configured)
    """
    try:
        # Try to get region from boto3 if not provided
        if region is None:
            region = _get_region_from_boto3()

        if region is None:
            raise ValueError(
                "Region must be provided or boto3 must be configured with a default region."
            )

        model_data = load_model_data()
        if model_id not in model_data:
            return False
        available_regions = model_data[model_id].get("regions", [])
        return region in available_regions
    except ValueError:
        raise
    except Exception:
        return False


def get_available_regions(model_id: str) -> list[str]:
    """
    Get the list of regions where a model is available.
    
    Args:
        model_id: The model ID
        
    Returns:
        List of AWS regions where the model is available
        
    Raises:
        ValueError: If model_id is not found
    """
    model_data = load_model_data()
    if model_id not in model_data:
        raise ValueError(f"Model ID '{model_id}' not found in bedrock_models.json")
    return model_data[model_id].get("regions", [])


def has_global_profile(model_id: str, region: str) -> bool:
    """
    Check if a model has a global inference profile available in a region.
    
    Args:
        model_id: The model ID
        region: The AWS region
        
    Returns:
        True if the model has GLOBAL inference type in the region, False otherwise
    """
    try:
        model_data = load_model_data()
        if model_id not in model_data:
            return False
        inference_types = model_data[model_id].get("inference_types", {}).get(region, [])
        return "GLOBAL" in inference_types
    except Exception:
        return False


def get_inference_profiles(model_id: str, region: str) -> list[str]:
    """
    Get all available inference profile prefixes for a model in a region.
    
    Args:
        model_id: The model ID
        region: The AWS region
        
    Returns:
        List of inference profile prefixes (e.g., ["US", "GLOBAL"], ["EU"], etc.)
        Returns empty list if model not found or no profiles available
        
    Example:
        >>> get_inference_profiles("anthropic.claude-3-5-sonnet-20241022-v2:0", "us-east-1")
        ["US", "GLOBAL"]
    """
    try:
        model_data = load_model_data()
        if model_id not in model_data:
            return []
        
        inference_types = model_data[model_id].get("inference_types", {}).get(region, [])
        
        # Filter to only profile prefixes (not ON_DEMAND or PROVISIONED)
        profile_prefixes = {"US", "EU", "CA", "JP", "AU", "APAC", "AP", "GLOBAL"}
        return [t for t in inference_types if t in profile_prefixes]
    except Exception:
        return []


def get_inference_types(model_id: str, region: str) -> list[str]:
    """
    Get all available inference types for a model in a region.
    
    Args:
        model_id: The model ID
        region: The AWS region
        
    Returns:
        List of inference types (e.g., ["ON_DEMAND", "US", "GLOBAL"], ["ON_DEMAND", "PROVISIONED"], etc.)
        Returns empty list if model not found
        
    Example:
        >>> get_inference_types("anthropic.claude-3-5-sonnet-20241022-v2:0", "us-east-1")
        ["ON_DEMAND", "US", "GLOBAL"]
    """
    try:
        model_data = load_model_data()
        if model_id not in model_data:
            return []
        
        return model_data[model_id].get("inference_types", {}).get(region, [])
    except Exception:
        return []





def cris_model_id(model_id: str, region: Optional[str] = None) -> str:
    """
    Get the cross-region inference (CRIS) model ID for a model.
    Returns geo-specific CRIS if supported in the region, otherwise returns global CRIS.

    Args:
        model_id: The model ID
        region: The AWS region. If not provided, will attempt to get from boto3 session.

    Returns:
        The CRIS model ID (geo-specific or global)

    Examples:
        >>> cris_model_id("anthropic.claude-3-5-sonnet-20241022-v2:0", region="us-east-1")
        "us.anthropic.claude-3-5-sonnet-20241022-v2:0"

        >>> # If geo CRIS not supported but global is available
        >>> cris_model_id("some.model-v1:0", region="us-east-1")
        "global.some.model-v1:0"

    Raises:
        ValueError: If region cannot be determined
        ValueError: If model is not available in the region
        ValueError: If neither geo nor global CRIS is supported
    """
    # Try to get region from boto3 if not provided
    if region is None:
        region = _get_region_from_boto3()

    if region is None:
        raise ValueError(
            "Region must be provided or boto3 must be configured with a default region."
        )

    # Load model data
    model_data = load_model_data()

    # Validate model exists
    if model_id not in model_data:
        raise ValueError(f"Model ID '{model_id}' not found in bedrock_models.json")

    # Check if model is available in the region
    available_regions = model_data[model_id].get("regions", [])
    if region not in available_regions:
        raise ValueError(
            f"Model '{model_id}' is not available in region '{region}'. "
            f"Available regions: {', '.join(available_regions)}"
        )

    # Check inference types for this region
    inference_types = model_data[model_id].get("inference_types", {}).get(region, [])

    
    # Check for geo-specific profile first (prefer regional over global)
    available_geo_profiles = [t for t in inference_types if t != "GLOBAL"]
    if available_geo_profiles:
        # Use the first available geo-specific profile (typically there's only one per region)
        prefix = available_geo_profiles[0].lower()
        return f"{prefix}.{model_id}"

    # Check if GLOBAL is available
    if "GLOBAL" in inference_types:
        return f"global.{model_id}"

    # Neither geo nor global CRIS is supported
    raise ValueError(
        f"Model '{model_id}' does not support CRIS in region '{region}'. "
        f"Available inference types: {', '.join(inference_types)}"
    )


def global_model_id(model_id: str, region: Optional[str] = None) -> str:
    """
    Get the global inference profile ID for a model if supported in the region.

    Args:
        model_id: The model ID
        region: The AWS region. If not provided, will attempt to get from boto3 session.

    Returns:
        The global inference profile ID in format: global.{model_id}

    Example:
        >>> global_model_id("anthropic.claude-3-5-sonnet-20241022-v2:0", region="us-east-1")
        "global.anthropic.claude-3-5-sonnet-20241022-v2:0"

    Raises:
        ValueError: If region cannot be determined
        ValueError: If model is not available in the region
        ValueError: If global inference profile is not supported in the region
    """
    # Try to get region from boto3 if not provided
    if region is None:
        region = _get_region_from_boto3()

    if region is None:
        raise ValueError(
            "Region must be provided or boto3 must be configured with a default region."
        )

    # Check if model has global profile in this region
    if not has_global_profile(model_id, region):
        # Load model data for better error message
        model_data = load_model_data()
        if model_id not in model_data:
            raise ValueError(f"Model ID '{model_id}' not found in bedrock_models.json")

        available_regions = model_data[model_id].get("regions", [])
        if region not in available_regions:
            raise ValueError(
                f"Model '{model_id}' is not available in region '{region}'. "
                f"Available regions: {', '.join(available_regions)}"
            )

        inference_types = model_data[model_id].get("inference_types", {}).get(
            region, []
        )
        raise ValueError(
            f"Model '{model_id}' does not support global inference profile in region '{region}'. "
            f"Available inference types: {', '.join(inference_types)}"
        )

    return f"global.{model_id}"
