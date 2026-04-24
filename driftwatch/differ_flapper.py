"""Flap detection: identify resources that oscillate between drifted and clean states."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from driftwatch.history import load as load_history


@dataclass
class FlapEntry:
    resource_id: str
    kind: str
    provider: str
    flap_count: int
    run_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "kind": self.kind,
            "provider": self.provider,
            "flap_count": self.flap_count,
            "run_ids": self.run_ids,
        }


@dataclass
class FlapReport:
    entries: list[FlapEntry] = field(default_factory=list)
    threshold: int = 2

    def to_dict(self) -> dict[str, Any]:
        return {
            "threshold": self.threshold,
            "flapping_resources": [e.to_dict() for e in self.entries],
            "total": len(self.entries),
        }


def detect_flapping(history_file: str, threshold: int = 2) -> FlapReport:
    """Scan drift history and return resources that flapped >= threshold times."""
    entries = load_history(history_file)
    if not entries:
        return FlapReport(threshold=threshold)

    # Map resource_id -> list of (run_id, change_type)
    seen: dict[str, dict[str, Any]] = {}

    for history_entry in entries:
        run_id = history_entry.get("run_id", "")
        drift = history_entry.get("drift", {})
        for entry in drift.get("entries", []):
            rid = entry.get("resource_id", "")
            kind = entry.get("kind", "")
            provider = entry.get("provider", "")
            key = f"{provider}:{kind}:{rid}"
            if key not in seen:
                seen[key] = {
                    "resource_id": rid,
                    "kind": kind,
                    "provider": provider,
                    "run_ids": [],
                }
            if run_id and run_id not in seen[key]["run_ids"]:
                seen[key]["run_ids"].append(run_id)

    flap_entries = []
    for meta in seen.values():
        count = len(meta["run_ids"])
        if count >= threshold:
            flap_entries.append(
                FlapEntry(
                    resource_id=meta["resource_id"],
                    kind=meta["kind"],
                    provider=meta["provider"],
                    flap_count=count,
                    run_ids=list(meta["run_ids"]),
                )
            )

    flap_entries.sort(key=lambda e: e.flap_count, reverse=True)
    return FlapReport(entries=flap_entries, threshold=threshold)
