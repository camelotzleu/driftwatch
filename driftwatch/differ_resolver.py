"""Drift resolver: mark drift entries as resolved with optional notes."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from driftwatch.differ import DriftEntry, DriftReport


@dataclass
class ResolvedEntry:
    entry: DriftEntry
    resolved_at: str
    resolved_by: str
    note: str

    def to_dict(self) -> dict:
        return {
            "resource_id": self.entry.resource_id,
            "kind": self.entry.kind,
            "provider": self.entry.provider,
            "change_type": self.entry.change_type,
            "resolved_at": self.resolved_at,
            "resolved_by": self.resolved_by,
            "note": self.note,
        }


@dataclass
class ResolutionReport:
    resolved: List[ResolvedEntry] = field(default_factory=list)
    unresolved: List[DriftEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "resolved": [r.to_dict() for r in self.resolved],
            "unresolved": [
                {
                    "resource_id": e.resource_id,
                    "kind": e.kind,
                    "provider": e.provider,
                    "change_type": e.change_type,
                }
                for e in self.unresolved
            ],
            "total_resolved": len(self.resolved),
            "total_unresolved": len(self.unresolved),
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_report(
    report: DriftReport,
    resource_ids: List[str],
    resolved_by: str = "unknown",
    note: str = "",
    resolved_at: Optional[str] = None,
) -> ResolutionReport:
    """Split a DriftReport into resolved and unresolved entries."""
    ts = resolved_at or _now_iso()
    id_set = set(resource_ids)
    result = ResolutionReport()
    for entry in report.entries:
        if entry.resource_id in id_set:
            result.resolved.append(
                ResolvedEntry(
                    entry=entry,
                    resolved_at=ts,
                    resolved_by=resolved_by,
                    note=note,
                )
            )
        else:
            result.unresolved.append(entry)
    return result
