from __future__ import annotations

import pytest

from driftwatch.config import ProviderConfig
from driftwatch.collectors import get_collector
from driftwatch.collectors.mock_collector import MockCollector
from driftwatch.collectors.aws_collector import AWSCollector
from driftwatch.collectors.gcp_collector import GCPCollector
from driftwatch.collectors.azure_collector import AzureCollector


def _cfg(provider: str) -> ProviderConfig:
    return ProviderConfig(provider=provider, label=f"test-{provider}")


@pytest.fixture
def mock_config() -> ProviderConfig:
    return _cfg("mock")


def test_get_collector_returns_mock(mock_config):
    collector = get_collector(mock_config)
    assert isinstance(collector, MockCollector)


def test_get_collector_returns_aws():
    collector = get_collector(_cfg("aws"))
    assert isinstance(collector, AWSCollector)


def test_get_collector_returns_gcp():
    collector = get_collector(_cfg("gcp"))
    assert isinstance(collector, GCPCollector)


def test_get_collector_returns_azure():
    collector = get_collector(_cfg("azure"))
    assert isinstance(collector, AzureCollector)


def test_get_collector_unknown_provider():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_collector(_cfg("digitalocean"))


def test_mock_collector_provider_name(mock_config):
    collector = get_collector(mock_config)
    assert collector.provider_name == "mock"


def test_azure_collector_provider_name():
    collector = get_collector(_cfg("azure"))
    assert collector.provider_name == "azure"


def test_collector_label_propagated():
    cfg = ProviderConfig(provider="mock", label="my-mock")
    collector = get_collector(cfg)
    snapshot = collector.collect()
    assert snapshot.label == "my-mock"
