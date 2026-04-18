from abc import ABC, abstractmethod
from driftwatch.snapshot import Snapshot, ResourceSnapshot


class BaseCollector(ABC):
    """Abstract base class for resource collectors."""

    def __init__(self, provider_config):
        self.config = provider_config

    @abstractmethod
    def collect(self) -> Snapshot:
        """Collect resources and return a Snapshot."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier string."""
        ...

    def _make_snapshot(self, resources: list[dict]) -> Snapshot:
        snap = Snapshot(provider=self.provider_name)
        for r in resources:
            rs = ResourceSnapshot(
                resource_id=r["id"],
                resource_type=r["type"],
                attributes=r.get("attributes", {}),
            )
            snap.add(rs)
        return snap
