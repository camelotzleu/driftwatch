"""Tests for the collector registry (get_collector)."""
from __future__ import annotations

import pytest

from driftwatch.config import ProviderConfig
from driftwatch.collectors import get_collector
from driftwatch.collectors.mock_collector import MockCollector


def _cfg(provider: str, **kw) -> ProviderConfig:
    return ProviderConfig(provider=provider, region="us-east-1", profile=None, enabled=True, **kw)


@pytest.fixture
def mock_config() -> ProviderConfig:
    return _cfg("mock")


def test_get_collector_returns_mock(mock_config):
    collector = get_collector(mock_config)
    assert isinstance(collector, MockCollector)


def test_get_collector_unknown_provider():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_collector(_cfg("gcp"))


def test_mock_collector_provider_name(mock_config):
    assert get_collector(mock_config).provider_name == "mock"


def test_mock_collector_collect_returns_snapshot(mock_config):
    from driftwatch.snapshot import Snapshot
    snapshot = get_collector(mock_config).collect()
    assert isinstance(snapshot, Snapshot)


def test_mock_collector_snapshot_has_resources(mock_config):
    snapshot = get_collector(mock_config).collect()
    resources = snapshot.to_dict()["resources"]
    assert len(resources) > 0


def test_mock_collector_resource_types(mock_config):
    snapshot = get_collector(mock_config).collect()
    types = {r["resource_type"] for r in snapshot.to_dict()["resources"]}
    assert len(types) >= 1


def test_get_collector_aws_registered():
    """AWS collector should be in the registry when boto3 is importable."""
    try:
        import boto3  # noqa: F401
        boto3_available = True
    except ImportError:
        boto3_available = False

    if boto3_available:
        from driftwatch.collectors.aws_collector import AWSCollector
        collector = get_collector(_cfg("aws"))
        assert isinstance(collector, AWSCollector)
    else:
        pytest.skip("boto3 not installed")
