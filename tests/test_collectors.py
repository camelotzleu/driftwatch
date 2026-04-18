import pytest
from unittest.mock import MagicMock
from driftwatch.collectors import get_collector, COLLECTOR_REGISTRY
from driftwatch.collectors.mock_collector import MockCollector
from driftwatch.snapshot import Snapshot


@pytest.fixture
def mock_config():
    cfg = MagicMock()
    cfg.region = "us-east-1"
    return cfg


def test_get_collector_returns_mock(mock_config):
    collector = get_collector("mock", mock_config)
    assert isinstance(collector, MockCollector)


def test_get_collector_unknown_provider(mock_config):
    with pytest.raises(ValueError, match="Unknown provider"):
        get_collector("nonexistent", mock_config)


def test_mock_collector_provider_name(mock_config):
    collector = MockCollector(mock_config)
    assert collector.provider_name == "mock"


def test_mock_collector_collect_returns_snapshot(mock_config):
    collector = MockCollector(mock_config)
    snap = collector.collect()
    assert isinstance(snap, Snapshot)
    assert snap.provider == "mock"


def test_mock_collector_collect_resource_count(mock_config):
    collector = MockCollector(mock_config)
    snap = collector.collect()
    assert len(snap.resources) == len(MockCollector.MOCK_RESOURCES)


def test_mock_collector_resource_ids(mock_config):
    collector = MockCollector(mock_config)
    snap = collector.collect()
    ids = {r.resource_id for r in snap.resources.values()}
    expected = {r["id"] for r in MockCollector.MOCK_RESOURCES}
    assert ids == expected


def test_registry_contains_mock():
    assert "mock" in COLLECTOR_REGISTRY
