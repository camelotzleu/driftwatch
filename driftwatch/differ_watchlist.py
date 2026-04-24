"""Watchlist: flag drift entries whose resource IDs are on a watch list."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from driftwatch.differ import DriftEntry, DriftReport


@dataclass
class WatchlistEntry:
    resource_id: str
    reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {"resource_id": self.resource_id, "reason": self.reason}


@dataclass
class WatchedDriftEntry:
    entry: DriftEntry
    reason: Optional[str]

    def to_dict(self) -> dict:
        return {
            "resource_id": self.entry.resource_id,
            "kind": self.entry.kind,
            "provider": self.entry.provider,
            "change_type": self.entry.change_type,
            "reason": self.reason,
        }


@dataclass
class WatchlistReport:
    watched: List[WatchedDriftEntry] = field(default_factory=list)
    total_checked: int = 0

    def to_dict(self) -> dict:
        return {
            "total_checked": self.total_checked,
            "watched_hits": len(self.watched),
            "entries": [e.to_dict() for e in self.watched],
        }


def _build_index(watchlist: List[WatchlistEntry]) -> dict:
    return {w.resource_id: w.reason for w in watchlist}


def check_watchlist(
    report: DriftReport, watchlist: List[WatchlistEntry]
) -> WatchlistReport:
    """Return a WatchlistReport of drift entries whose resource IDs are watched."""
    index = _build_index(watchlist)
    result = WatchlistReport(total_checked=len(report.entries))
    for entry in report.entries:
        if entry.resource_id in index:
            result.watched.append(
                WatchedDriftEntry(entry=entry, reason=index[entry.resource_id])
            )
    return result


def watchlist_from_dicts(items: List[dict]) -> List[WatchlistEntry]:
    """Build a watchlist from a list of plain dicts (e.g. from config YAML)."""
    return [
        WatchlistEntry(
            resource_id=item["resource_id"],
            reason=item.get("reason"),
        )
        for item in items
        if "resource_id" in item
    ]
