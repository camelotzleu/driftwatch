"""Expiry detection: flag drift entries that have persisted beyond a TTL."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from driftwatch.differ import DriftReport, DriftEntry
from driftwatch.history import load as load_history


@dataclass
class ExpiredEntry:
    entry: DriftEntry
    first_seen: str
    age_days: float
    ttl_days: int
    expired: bool

    def to_dict(self) -> dict:
        return {
            "resource_id": self.entry.resource_id,
            "kind": self.entry.kind,
            "provider": self.entry.provider,
            "change_type": self.entry.change_type,
            "first_seen": self.first_seen,
            "age_days": round(self.age_days, 2),
            "ttl_days": self.ttl_days,
            "expired": self.expired,
        }


@dataclass
class ExpiryReport:
    entries: List[ExpiredEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total": len(self.entries),
            "expired_count": sum(1 for e in self.entries if e.expired),
            "entries": [e.to_dict() for e in self.entries],
        }


def _first_seen_for(resource_id: str, history: list) -> Optional[str]:
    """Return ISO timestamp of the first history run containing resource_id."""
    for run in history:
        report = run.get("report", {})
        for entry in report.get("entries", []):
            if entry.get("resource_id") == resource_id:
                return run.get("timestamp")
    return None


def _age_days(first_seen_iso: str) -> float:
    first = datetime.fromisoformat(first_seen_iso.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return (now - first).total_seconds() / 86400.0


def check_expiry(report: DriftReport, ttl_days: int = 7) -> ExpiryReport:
    """Cross-reference each drift entry against history to detect stale drift."""
    history = load_history() or []
    result = ExpiryReport()

    for entry in report.entries:
        first_seen = _first_seen_for(entry.resource_id, history)
        if first_seen is None:
            age = 0.0
            expired = False
        else:
            age = _age_days(first_seen)
            expired = age > ttl_days

        result.entries.append(
            ExpiredEntry(
                entry=entry,
                first_seen=first_seen or "",
                age_days=age,
                ttl_days=ttl_days,
                expired=expired,
            )
        )

    return result
