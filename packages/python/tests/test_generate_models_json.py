"""Tests for the model generator's retry classification and failure fallback."""

import socket
import ssl
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

UTILS_DIR = str(Path(__file__).parent.parent / "utils")
if UTILS_DIR not in sys.path:
    sys.path.append(UTILS_DIR)

gen = pytest.importorskip("generate_models_json")


def _throttle():
    return ClientError({"Error": {"Code": "ThrottlingException", "Message": "slow down"}}, "GetInferenceProfile")


@pytest.mark.parametrize("exc", [
    urllib.error.URLError(socket.gaierror(socket.EAI_NONAME, "Name or service not known")),
    socket.gaierror(socket.EAI_NONAME, "Name or service not known"),
    urllib.error.URLError(ssl.SSLCertVerificationError("certificate verify failed")),
    urllib.error.HTTPError("u", 404, "nf", {}, None),
    ClientError({"Error": {"Code": "AccessDeniedException"}}, "Op"),
])
def test_non_retryable(exc):
    assert not gen._is_retryable(exc)


@pytest.mark.parametrize("exc", [
    urllib.error.URLError(socket.gaierror(socket.EAI_AGAIN, "Temporary failure in name resolution")),
    urllib.error.URLError(socket.timeout("timed out")),
    urllib.error.URLError(ConnectionResetError()),
    urllib.error.HTTPError("u", 503, "unavailable", {}, None),
    _throttle(),
    TimeoutError(),
])
def test_retryable(exc):
    assert gen._is_retryable(exc)


def test_dns_failure_is_not_retried():
    func = MagicMock(side_effect=urllib.error.URLError(socket.gaierror(-2, "Name or service not known")))
    with pytest.raises(urllib.error.URLError):
        gen.retry_on_timeout(func, base_delay=0)
    assert func.call_count == 1


def test_mantle_unresolvable_host_returns_empty_not_failed():
    with patch.object(gen, "provide_token", return_value="t"), \
         patch.object(gen.urllib.request, "urlopen",
                      side_effect=urllib.error.URLError(socket.gaierror(-2, "Name or service not known"))) as uo:
        assert gen.get_mantle_models_in_region("us-west-1") == ({}, set())
    assert uo.call_count == 1


def test_inference_profile_lookup_exhausted_is_reported_as_failed():
    client = MagicMock()
    client.list_inference_profiles.return_value = {"inferenceProfileSummaries": [
        {"inferenceProfileId": "global.anthropic.model-x"},
        {"inferenceProfileId": "us.anthropic.model-x"},
    ]}

    def get_profile(inferenceProfileIdentifier):
        if inferenceProfileIdentifier.startswith("global."):
            raise _throttle()
        return {"models": [{"modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.model-x"}]}

    client.get_inference_profile.side_effect = get_profile
    with patch.object(gen, "make_bedrock_client", return_value=client), patch.object(gen.time, "sleep"):
        profiles, failed = gen.get_inference_profiles_in_region("us-west-2")

    assert profiles == {"anthropic.model-x": {"GLOBAL": [], "US": ["us-east-1"]}}
    assert failed == {("anthropic.model-x", "GLOBAL")}


def test_merge_restores_profiles_after_failed_lookup():
    old_models = {"model-x": {
        "regions": ["us-west-2"],
        "inference_types": {"us-west-2": ["GLOBAL", "US"]},
        "inferenceProfile": {
            "GLOBAL": ["eu-west-2", "us-east-1", "us-west-2"],
            "US": {"us-west-2": ["us-east-1", "us-west-2"]},
        },
    }}
    # Degraded scan: GLOBAL lookup in us-west-2 lost eu-west-2, US lookup returned [].
    current = {"model-x": {
        "regions": ["us-west-2"],
        "inference_types": {"us-west-2": ["GLOBAL", "US"]},
        "inferenceProfile": {
            "GLOBAL": ["us-east-1", "us-west-2"],
            "US": {"us-west-2": []},
        },
    }}
    gen.merge_failed_regions_from_previous(
        current, set(), old_models, set(),
        {("model-x", "GLOBAL", "us-west-2"), ("model-x", "US", "us-west-2")},
    )
    assert current["model-x"]["inferenceProfile"] == old_models["model-x"]["inferenceProfile"]


def test_merge_does_not_touch_profiles_without_failures():
    old_models = {"model-x": {"regions": ["us-west-2"], "inference_types": {},
                              "inferenceProfile": {"GLOBAL": ["eu-west-2", "us-west-2"]}}}
    current = {"model-x": {"regions": ["us-west-2"], "inference_types": {},
                           "inferenceProfile": {"GLOBAL": ["us-west-2"]}}}
    gen.merge_failed_regions_from_previous(current, set(), old_models, set(), set())
    assert current["model-x"]["inferenceProfile"]["GLOBAL"] == ["us-west-2"]
