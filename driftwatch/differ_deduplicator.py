"""Deduplicates drift entries across multiple reports by resource identity."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from driftwatch.differ import DriftEntry, DriftReport


def _entry_key(e: DriftEntry) -> Tuple[str, str, str]:
    return (e.provider, e.resource_id, e.kind)


@dataclass
class DeduplicatedReport:
    entries: List[DriftEntry] = field(default_factory=list)
    duplicate_count: int = 0

    def to_dict(self) -> Dict:
        return {
            "entries": [
                {
                    "provider": e.provider,
                    "resource_id": e.resource_id,
                    "kind": e.kind,
                    "change_type": e.change_type,
                    "attribute_diff": e.attribute_diff,
                }
                for e in self.entries
            ],
            "total": len(self.entries),
            "duplicates_removed": self.duplicate_count,
        }


def deduplicate_reports(reports: List[DriftReport]) -> DeduplicatedReport:
    """Merge multiple DriftReports, keeping only the first occurrence of each resource."""
    seen: Dict[Tuple[str, str, str], DriftEntry] = {}
    duplicate_count = 0

    for report in reports:
        for entry in report.entries:
            key = _entry_key(entry)
            if key in seen:
                duplicate_count += 1
            else:
                seen[key] = entry

    return DeduplicatedReport(
        entries=list(seen.values()),
        duplicate_count=duplicate_count,
    )
