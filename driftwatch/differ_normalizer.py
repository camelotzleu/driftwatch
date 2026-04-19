"""Normalize drift entries: trim whitespace, lowercase keys, cast types."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from driftwatch.differ import DriftReport, DriftEntry


@dataclass
class NormalizedEntry:
    entry: DriftEntry
    changes: dict[str, str] = field(default_factory=dict)  # field -> description

    def to_dict(self) -> dict:
        return {
            "resource_id": self.entry.resource_id,
            "kind": self.entry.kind,
            "provider": self.entry.provider,
            "change_type": self.entry.change_type,
            "normalizations": self.changes,
        }


@dataclass
class NormalizedReport:
    entries: list[NormalizedEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"normalized": [e.to_dict() for e in self.entries]}


def _normalize_value(v: Any) -> tuple[Any, str | None]:
    """Return (normalized_value, description_of_change) or (v, None)."""
    if isinstance(v, str):
        stripped = v.strip()
        lowered = stripped.lower()
        if lowered != v:
            return lowered, f"trimmed/lowercased '{v}' -> '{lowered}'"
    if isinstance(v, float) and v == int(v):
        return int(v), f"cast float {v} -> int {int(v)}"
    return v, None


def _normalize_entry(entry: DriftEntry) -> NormalizedEntry:
    changes: dict[str, str] = {}
    if entry.attribute_diff:
        for attr_key, diff in entry.attribute_diff.items():
            for side in ("before", "after"):
                raw = diff.get(side)
                if raw is None:
                    continue
                normalized, desc = _normalize_value(raw)
                if desc:
                    changes[f"{attr_key}.{side}"] = desc
                    diff[side] = normalized
    return NormalizedEntry(entry=entry, changes=changes)


def normalize_report(report: DriftReport) -> NormalizedReport:
    """Normalize all entries in a DriftReport in-place and return a NormalizedReport."""
    return NormalizedReport(entries=[_normalize_entry(e) for e in report.entries])
