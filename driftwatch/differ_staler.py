"""Staleness detection: flag drift entries that have not changed state for too long."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.history import load as load_history


@dataclass
class StaleEntry:
    entry: DriftEntry
    first_seen: str
    days_stale: float
    is_stale: bool

    def to_dict(self) -> dict:
        return {
            "resource_id": self.entry.resource_id,
            "kind": self.entry.kind,
            "provider": self.entry.provider,
            "change_type": self.entry.change_type,
            "first_seen": self.first_seen,
            "days_stale": round(self.days_stale, 2),
            "is_stale": self.is_stale,
        }


@dataclass
class StalenessReport:
    entries: List[StaleEntry] = field(default_factory=list)
    threshold_days: float = 7.0

    def to_dict(self) -> dict:
        return {
            "threshold_days": self.threshold_days,
            "total": len(self.entries),
            "stale_count": sum(1 for e in self.entries if e.is_stale),
            "entries": [e.to_dict() for e in self.entries],
        }


def _first_seen_for(resource_id: str, kind: str, provider: str) -> Optional[str]:
    """Return the ISO timestamp when this resource first appeared in history."""
    history = load_history()
    for run in history:
        for entry in run.get("entries", []):
            if (
                entry.get("resource_id") == resource_id
                and entry.get("kind") == kind
                and entry.get("provider") == provider
            ):
                return run.get("timestamp")
    return None


def _days_since(iso_timestamp: str) -> float:
    try:
        then = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return 0.0
    now = datetime.now(tz=timezone.utc)
    return (now - then).total_seconds() / 86400.0


def detect_stale(report: DriftReport, threshold_days: float = 7.0) -> StalenessReport:
    """Evaluate each drift entry and mark those stale beyond threshold_days."""
    result = StalenessReport(threshold_days=threshold_days)
    for entry in report.entries:
        first_seen = _first_seen_for(entry.resource_id, entry.kind, entry.provider)
        if first_seen is None:
            days = 0.0
        else:
            days = _days_since(first_seen)
        stale = first_seen is not None and days >= threshold_days
        result.entries.append(
            StaleEntry(
                entry=entry,
                first_seen=first_seen or "",
                days_stale=days,
                is_stale=stale,
            )
        )
    return result
