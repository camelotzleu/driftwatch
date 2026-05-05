"""Aggregate drift entries across multiple reports into a unified view."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any

from driftwatch.differ import DriftReport, DriftEntry


@dataclass
class AggregatedEntry:
    resource_id: str
    kind: str
    provider: str
    change_type: str
    occurrences: int
    sources: List[str]  # report labels / origins
    attribute_diff: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "kind": self.kind,
            "provider": self.provider,
            "change_type": self.change_type,
            "occurrences": self.occurrences,
            "sources": self.sources,
            "attribute_diff": self.attribute_diff,
        }


@dataclass
class AggregationReport:
    entries: List[AggregatedEntry] = field(default_factory=list)
    total_reports: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_reports": self.total_reports,
            "total_entries": len(self.entries),
            "entries": [e.to_dict() for e in self.entries],
        }


def _entry_key(entry: DriftEntry) -> str:
    return f"{entry.provider}::{entry.kind}::{entry.resource_id}::{entry.change_type}"


def aggregate_reports(
    reports: List[DriftReport],
    labels: List[str] | None = None,
) -> AggregationReport:
    """Merge multiple DriftReports, counting co-occurrences."""
    if labels is None:
        labels = [f"report_{i}" for i in range(len(reports))]

    seen: Dict[str, AggregatedEntry] = {}

    for label, report in zip(labels, reports):
        for entry in report.entries:
            key = _entry_key(entry)
            if key in seen:
                agg = seen[key]
                agg.occurrences += 1
                if label not in agg.sources:
                    agg.sources.append(label)
            else:
                seen[key] = AggregatedEntry(
                    resource_id=entry.resource_id,
                    kind=entry.kind,
                    provider=entry.provider,
                    change_type=entry.change_type,
                    occurrences=1,
                    sources=[label],
                    attribute_diff=entry.attribute_diff or {},
                )

    return AggregationReport(
        entries=list(seen.values()),
        total_reports=len(reports),
    )
