from driftwatch.collectors.base import BaseCollector
from driftwatch.snapshot import Snapshot


class MockCollector(BaseCollector):
    """Collector that returns a static snapshot — useful for testing and demos."""

    MOCK_RESOURCES = [
        {
            "id": "instance-001",
            "type": "compute.instance",
            "attributes": {"state": "running", "size": "t3.micro", "region": "us-east-1"},
        },
        {
            "id": "bucket-logs",
            "type": "storage.bucket",
            "attributes": {"versioning": True, "public": False, "region": "us-east-1"},
        },
        {
            "id": "sg-web",
            "type": "network.security_group",
            "attributes": {"inbound_ports": [80, 443], "region": "us-east-1"},
        },
    ]

    @property
    def provider_name(self) -> str:
        return "mock"

    def collect(self) -> Snapshot:
        return self._make_snapshot(self.MOCK_RESOURCES)
