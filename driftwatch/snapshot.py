"""Snapshot module for capturing and storing cloud resource state."""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ResourceSnapshot:
    provider: str
    resource_type: str
    resource_id: str
    attributes: dict[str, Any]
    captured_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def fingerprint(self) -> str:
        """SHA-256 hash of the resource attributes for drift comparison."""
        payload = json.dumps(self.attributes, sort_keys=True).encode()
        return hashlib.sha256(payload).hexdigest()


@dataclass
class Snapshot:
    label: str
    resources: list[ResourceSnapshot] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add(self, resource: ResourceSnapshot) -> None:
        self.resources.append(resource)

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "created_at": self.created_at,
            "resources": [asdict(r) for r in self.resources],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Snapshot":
        resources = [
            ResourceSnapshot(**r) for r in data.get("resources", [])
        ]
        return cls(
            label=data["label"],
            resources=resources,
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        )

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path) -> "Snapshot":
        data = json.loads(path.read_text())
        return cls.from_dict(data)
