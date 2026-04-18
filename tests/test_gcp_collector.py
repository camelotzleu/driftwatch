"""Tests for GCPCollector using a mocked Google API client."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from driftwatch.collectors.gcp_collector import GCPCollector
from driftwatch.config import ProviderConfig


def _make_config(**kwargs) -> ProviderConfig:
    defaults = {"name": "gcp-test", "provider": "gcp", "project_id": "my-project"}
    defaults.update(kwargs)
    return ProviderConfig(**defaults)


def _fake_instance(name: str = "vm-1", status: str = "RUNNING") -> dict:
    return {
        "id": f"123456-{name}",
        "name": name,
        "status": status,
        "machineType": "zones/us-central1-a/machineTypes/n1-standard-1",
        "zone": "projects/my-project/zones/us-central1-a",
        "tags": {"items": ["http-server", "https-server"]},
        "labels": {"env": "prod"},
        "networkInterfaces": [{"network": "global/networks/default"}],
    }


def _build_mock_service(instances: list) -> MagicMock:
    aggregated_response = {
        "items": {"zones/us-central1-a": {"instances": instances}}
    }
    mock_request = MagicMock()
    mock_request.execute.return_value = aggregated_response

    mock_instances = MagicMock()
    mock_instances.aggregatedList.return_value = mock_request
    mock_instances.aggregatedList_next.return_value = None

    mock_service = MagicMock()
    mock_service.instances.return_value = mock_instances
    return mock_service


@patch("driftwatch.collectors.gcp_collector.googleapiclient", create=True)
def test_collect_returns_snapshot(mock_gapi):
    cfg = _make_config()
    collector = GCPCollector(cfg)

    fake = _fake_instance()
    mock_service = _build_mock_service([fake])

    with patch("googleapiclient.discovery.build", return_value=mock_service), \
         patch("google.oauth2.service_account.Credentials", create=True), \
         patch.dict("sys.modules", {
             "googleapiclient": MagicMock(),
             "googleapiclient.discovery": MagicMock(build=MagicMock(return_value=mock_service)),
             "google.oauth2": MagicMock(),
             "google.oauth2.service_account": MagicMock(),
         }):
        snapshot = collector.collect()

    assert snapshot is not None
    assert snapshot.provider == "gcp"


def test_extract_attributes():
    cfg = _make_config()
    collector = GCPCollector(cfg)
    instance = _fake_instance("vm-2", "TERMINATED")
    attrs = collector._extract_attributes(instance)

    assert attrs["name"] == "vm-2"
    assert attrs["status"] == "TERMINATED"
    assert attrs["machine_type"] == "n1-standard-1"
    assert attrs["zone"] == "us-central1-a"
    assert attrs["tags"] == ["http-server", "https-server"]
    assert attrs["labels"] == {"env": "prod"}
    assert attrs["network_interfaces"] == ["default"]


def test_provider_name():
    cfg = _make_config()
    collector = GCPCollector(cfg)
    assert collector.provider_name == "gcp"


def test_missing_project_id_raises():
    cfg = ProviderConfig(name="gcp-noproj", provider="gcp")
    collector = GCPCollector(cfg)
    with patch.dict("sys.modules", {
        "googleapiclient": MagicMock(),
        "googleapiclient.discovery": MagicMock(),
        "google.oauth2": MagicMock(),
        "google.oauth2.service_account": MagicMock(),
    }):
        with pytest.raises((ValueError, Exception)):
            collector.collect()
