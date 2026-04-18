from driftwatch.collectors.base import BaseCollector
from driftwatch.snapshot import Snapshot
from driftwatch.config import ProviderConfig


class AzureCollector(BaseCollector):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client = None

    @property
    def provider_name(self) -> str:
        return "azure"

    def _get_client(self):
        if self._client is None:
            try:
                from azure.mgmt.compute import ComputeManagementClient
                from azure.identity import DefaultAzureCredential
                credential = DefaultAzureCredential()
                subscription_id = self.config.credentials.get("subscription_id", "")
                self._client = ComputeManagementClient(credential, subscription_id)
            except ImportError:
                raise RuntimeError("azure-mgmt-compute and azure-identity are required for Azure support")
        return self._client

    def collect(self, client=None) -> Snapshot:
        snapshot = self._make_snapshot()
        c = client or self._get_client()
        resource_group = self.config.credentials.get("resource_group", "")
        vms = c.virtual_machines.list(resource_group) if resource_group else c.virtual_machines.list_all()
        for vm in vms:
            attrs = self._extract_attributes(vm)
            snapshot.add(str(vm.id), "azure_vm", attrs)
        return snapshot

    def _extract_attributes(self, vm) -> dict:
        attrs = {
            "name": vm.name,
            "location": getattr(vm, "location", None),
            "vm_size": None,
            "os_type": None,
            "tags": dict(vm.tags) if getattr(vm, "tags", None) else {},
        }
        hw = getattr(vm, "hardware_profile", None)
        if hw:
            attrs["vm_size"] = getattr(hw, "vm_size", None)
        storage = getattr(vm, "storage_profile", None)
        if storage:
            os_disk = getattr(storage, "os_disk", None)
            if os_disk:
                attrs["os_type"] = getattr(os_disk, "os_type", None)
        return attrs
