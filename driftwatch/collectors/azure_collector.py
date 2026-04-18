from __future__ import annotations

from typing import Any, Dict, List

from driftwatch.collectors.base import BaseCollector
from driftwatch.config import ProviderConfig
from driftwatch.snapshot import Snapshot


class AzureCollector(BaseCollector):
    """Collector for Azure virtual machine instances."""

    @property
    def provider_name(self) -> str:
        return "azure"

    def collect(self) -> Snapshot:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.compute import ComputeManagementClient
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "azure-mgmt-compute and azure-identity packages are required for Azure collection"
            ) from exc

        snapshot = self._make_snapshot()
        subscription_id = self._config.extra.get("subscription_id", "")
        credential = DefaultAzureCredential()
        client = ComputeManagementClient(credential, subscription_id)

        for vm in client.virtual_machines.list_all():
            resource_id = vm.id or vm.name
            attrs = self._extract_attributes(vm)
            snapshot.add(resource_id=resource_id, resource_type="azure_vm", attributes=attrs)

        return snapshot

    def _extract_attributes(self, vm: Any) -> Dict[str, Any]:
        attrs: Dict[str, Any] = {}
        if vm.location:
            attrs["location"] = vm.location
        if vm.tags:
            attrs["tags"] = dict(vm.tags)
        if vm.hardware_profile:
            attrs["vm_size"] = vm.hardware_profile.vm_size
        if vm.storage_profile and vm.storage_profile.os_disk:
            attrs["os_disk_type"] = vm.storage_profile.os_disk.os_type
        if vm.os_profile:
            attrs["computer_name"] = vm.os_profile.computer_name
        if vm.provisioning_state:
            attrs["provisioning_state"] = vm.provisioning_state
        return attrs
