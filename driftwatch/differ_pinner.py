"""Drift pinning: mark specific drift entries as acknowledged/pinned so they
are excluded from future alert noise while still being recorded."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from driftwatch.differ import DriftEntry, DriftReport


def _pin_path(base_dir: str = ".") -> Path:
    return Path(base_dir) / ".driftwatch" / "pinned.json"


@dataclass
class PinnedEntry:
    resource_id: str
    kind: str
    provider: str
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "resource_id": self.resource_id,
            "kind": self.kind,
            "provider": self.provider,
            "reason": self.reason,
        }

    @staticmethod
    def from_dict(d: dict) -> "PinnedEntry":
        return PinnedEntry(
            resource_id=d["resource_id"],
            kind=d["kind"],
            provider=d["provider"],
            reason=d.get("reason", ""),
        )


@dataclass
class PinResult:
    pinned: List[DriftEntry] = field(default_factory=list)
    unpinned: List[DriftEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "pinned_count": len(self.pinned),
            "unpinned_count": len(self.unpinned),
            "unpinned": [
                {"resource_id": e.resource_id, "kind": e.kind, "provider": e.provider}
                for e in self.unpinned
            ],
        }


def _entry_is_pinned(entry: DriftEntry, pins: List[PinnedEntry]) -> bool:
    for pin in pins:
        if (
            pin.resource_id == entry.resource_id
            and pin.kind == entry.kind
            and pin.provider == entry.provider
        ):
            return True
    return False


def load_pins(base_dir: str = ".") -> List[PinnedEntry]:
    path = _pin_path(base_dir)
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    return [PinnedEntry.from_dict(d) for d in data]


def save_pins(pins: List[PinnedEntry], base_dir: str = ".") -> None:
    path = _pin_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([p.to_dict() for p in pins], indent=2))


def pin_report(report: DriftReport, pins: List[PinnedEntry]) -> PinResult:
    """Split report entries into pinned and unpinned."""
    result = PinResult()
    for entry in report.entries:
        if _entry_is_pinned(entry, pins):
            result.pinned.append(entry)
        else:
            result.unpinned.append(entry)
    return result
