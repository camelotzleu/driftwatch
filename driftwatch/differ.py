"""Differ module for comparing two snapshots and reporting drift."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from driftwatch.snapshot import Snapshot, ResourceSnapshot


@dataclass
class DriftEntry:
    resource_id: str
    resource_type: str
    provider: str
    status: str  # "added", "removed", "changed"
    diff: dict[str, Any]


@dataclass
class DriftReport:
    baseline_label: str
    current_label: str
    entries: list[DriftEntry]

    @property
    def has_drift(self) -> bool:
        return len(self.entries) > 0

    def summary(self) -> str:
        if not self.has_drift:
            return "No drift detected."
        lines = [f"Drift detected ({len(self.entries)} change(s)):\n"]
        for e in self.entries:
            lines.append(f"  [{e.status.upper()}] {e.provider}/{e.resource_type}/{e.resource_id}")
            for k, v in e.diff.items():
                lines.append(f"    {k}: {v}")
        return "\n".join(lines)


def _attribute_diff(baseline: dict, current: dict) -> dict[str, Any]:
    diff = {}
    all_keys = set(baseline) | set(current)
    for key in all_keys:
        b_val = baseline.get(key)
        c_val = current.get(key)
        if b_val != c_val:
            diff[key] = {"baseline": b_val, "current": c_val}
    return diff


def compare(baseline: Snapshot, current: Snapshot) -> DriftReport:
    """Compare two snapshots and return a DriftReport."""
    baseline_map: dict[str, ResourceSnapshot] = {
        r.resource_id: r for r in baseline.resources
    }
    current_map: dict[str, ResourceSnapshot] = {
        r.resource_id: r for r in current.resources
    }

    entries: list[DriftEntry] = []

    for rid, res in baseline_map.items():
        if rid not in current_map:
            entries.append(DriftEntry(rid, res.resource_type, res.provider, "removed", {}))
        elif res.fingerprint != current_map[rid].fingerprint:
            diff = _attribute_diff(res.attributes, current_map[rid].attributes)
            entries.append(DriftEntry(rid, res.resource_type, res.provider, "changed", diff))

    for rid, res in current_map.items():
        if rid not in baseline_map:
            entries.append(DriftEntry(rid, res.resource_type, res.provider, "added", {}))

    return DriftReport(baseline.label, current.label, entries)
