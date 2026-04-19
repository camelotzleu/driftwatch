"""Merge multiple DriftReports into a single consolidated report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from driftwatch.differ import DriftEntry, DriftReport


@dataclass
class MergeReport:
    sources: List[str]
    entries: List[DriftEntry]
    total: int
    duplicates_removed: int

    def to_dict(self) -> dict:
        return {
            "sources": self.sources,
            "total": self.total,
            "duplicates_removed": self.duplicates_removed,
            "entries": [
                {
                    "resource_id": e.resource_id,
                    "kind": e.kind,
                    "provider": e.provider,
                    "change_type": e.change_type,
                    "attribute_diff": e.attribute_diff,
                }
                for e in self.entries
            ],
        }


def _entry_key(e: DriftEntry) -> tuple:
    return (e.resource_id, e.provider, e.change_type)


def merge_reports(reports: List[DriftReport], sources: List[str] | None = None) -> MergeReport:
    """Merge a list of DriftReports, deduplicating by (resource_id, provider, change_type)."""
    if sources is None:
        sources = [f"report_{i}" for i in range(len(reports))]

    seen: dict[tuple, DriftEntry] = {}
    total_before = 0

    for report in reports:
        all_entries = report.added + report.removed + report.changed
        total_before += len(all_entries)
        for entry in all_entries:
            key = _entry_key(entry)
            if key not in seen:
                seen[key] = entry

    merged_entries = list(seen.values())
    duplicates_removed = total_before - len(merged_entries)

    return MergeReport(
        sources=sources,
        entries=merged_entries,
        total=len(merged_entries),
        duplicates_removed=duplicates_removed,
    )
