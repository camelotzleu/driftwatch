"""GCP collector — lists Compute Engine instances via the Google API client."""
from __future__ import annotations

from typing import Any, Dict, List

from driftwatch.collectors.base import BaseCollector
from driftwatch.config import ProviderConfig
from driftwatch.snapshot import Snapshot


class GCPCollector(BaseCollector):
    """Collect GCP Compute Engine instance snapshots."""

    @property
    def provider_name(self) -> str:
        return "gcp"

    def collect(self) -> Snapshot:
        snapshot = self._make_snapshot()
        try:
            import googleapiclient.discovery  # type: ignore
            from google.oauth2 import service_account  # type: ignore

            credentials = None
            if self.config.credentials_file:
                credentials = service_account.Credentials.from_service_account_file(
                    self.config.credentials_file,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )

            service = googleapiclient.discovery.build(
                "compute", "v1", credentials=credentials, cache_discovery=False
            )
            project = self.config.project_id
            if not project:
                raise ValueError("GCP provider requires 'project_id' in config")

            request = service.instances().aggregatedList(project=project)
            while request is not None:
                response = request.execute()
                for zone_data in response.get("items", {}).values():
                    for instance in zone_data.get("instances", []):
                        attrs = self._extract_attributes(instance)
                        snapshot.add(
                            resource_id=instance["id"],
                            resource_type="compute_instance",
                            attributes=attrs,
                        )
                request = service.instances().aggregatedList_next(
                    previous_request=request, previous_response=response
                )
        except ImportError as exc:
            raise RuntimeError(
                "google-api-python-client and google-auth are required for GCP collection"
            ) from exc
        return snapshot

    def _extract_attributes(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "name": instance.get("name"),
            "status": instance.get("status"),
            "machine_type": instance.get("machineType", "").split("/")[-1],
            "zone": instance.get("zone", "").split("/")[-1],
            "tags": sorted(instance.get("tags", {}).get("items", [])),
            "labels": instance.get("labels", {}),
            "network_interfaces": [
                ni.get("network", "").split("/")[-1]
                for ni in instance.get("networkInterfaces", [])
            ],
        }
