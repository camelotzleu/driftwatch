from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from driftwatch.config import ProviderConfig
from driftwatch.collectors.azure_collector import AzureCollector
from driftwatch.snapshot import Snapshot


def _make_config(extra=None) -> ProviderConfig:
    return ProviderConfig(
        provider="azure",
        label="test-azure",
        extra=extra or {"subscription_id": "sub-123"},
    )


def _fake_vm(
    vm_id="/subscriptions/sub-123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
    name="vm1",
    location="eastus",
    vm_size="Standard_D2s_v3",
    provisioning_state="Succeeded",
    tags=None,
):
    vm = MagicMock()
    vm.id = vm_id
    vm.name = name
    vm.location = location
    vm.tags = tags or {"env": "prod"}
    vm.hardware_profile.vm_size = vm_size
    vm.storage_profile.os_disk.os_type = "Linux"
    vm.os_profile.computer_name = name
    vm.provisioning_state = provisioning_state
    return vm


def _build_mock_client(vms):
    mock_client = MagicMock()
    mock_client.virtual_machines.list_all.return_value = iter(vms)
    return mock_client


@patch("driftwatch.collectors.azure_collector.DefaultAzureCredential")
@patch("driftwatch.collectors.azure_collector.ComputeManagementClient")
def test_collect_returns_snapshot(mock_client_cls, mock_cred_cls):
    mock_client_cls.return_value = _build_mock_client([_fake_vm()])
    collector = AzureCollector(_make_config())
    snapshot = collector.collect()
    assert isinstance(snapshot, Snapshot)
    assert len(snapshot.resources) == 1


@patch("driftwatch.collectors.azure_collector.DefaultAzureCredential")
@patch("driftwatch.collectors.azure_collector.ComputeManagementClient")
def test_collect_extracts_attributes(mock_client_cls, mock_cred_cls):
    vm = _fake_vm(location="westus", vm_size="Standard_B1s", tags={"team": "ops"})
    mock_client_cls.return_value = _build_mock_client([vm])
    collector = AzureCollector(_make_config())
    snapshot = collector.collect()
    res = list(snapshot.resources.values())[0]
    assert res.attributes["location"] == "westus"
    assert res.attributes["vm_size"] == "Standard_B1s"
    assert res.attributes["tags"] == {"team": "ops"}
    assert res.attributes["provisioning_state"] == "Succeeded"


@patch("driftwatch.collectors.azure_collector.DefaultAzureCredential")
@patch("driftwatch.collectors.azure_collector.ComputeManagementClient")
def test_collect_empty_subscription(mock_client_cls, mock_cred_cls):
    mock_client_cls.return_value = _build_mock_client([])
    collector = AzureCollector(_make_config())
    snapshot = collector.collect()
    assert snapshot.resources == {}


@patch("driftwatch.collectors.azure_collector.DefaultAzureCredential")
@patch("driftwatch.collectors.azure_collector.ComputeManagementClient")
def test_collect_multiple_vms(mock_client_cls, mock_cred_cls):
    vms = [_fake_vm(vm_id=f"/vm/{i}", name=f"vm{i}") for i in range(3)]
    mock_client_cls.return_value = _build_mock_client(vms)
    collector = AzureCollector(_make_config())
    snapshot = collector.collect()
    assert len(snapshot.resources) == 3


def test_provider_name():
    collector = AzureCollector(_make_config())
    assert collector.provider_name == "azure"
