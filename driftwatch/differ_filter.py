"""Utilities for filtering DriftReport entries by kind, provider, or resource id."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from driftwatch.differ import DriftEntry, DriftReport


@dataclass
class DriftFilter:
    kinds: List[str] = field(default_factory=list)          # e.g. ["changed", "added"]
    providers: List[str] = field(default_factory=list)       # e.g. ["aws", "gcp"]
    resource_ids: List[str] = field(default_factory=list)    # exact match
    resource_id_prefix: Optional[str] = None                 # prefix match


def _entry_matches(entry: DriftEntry, f: DriftFilter) -> bool:
    if f.kinds and entry.kind not in f.kinds:
        return False
    if f.providers and entry.provider not in f.providers:
        return False
    if f.resource_ids and entry.resource_id not in f.resource_ids:
        return False
    if f.resource_id_prefix and not entry.resource_id.startswith(f.resource_id_prefix):
        return False
    return True


def filter_report(report: DriftReport, f: DriftFilter) -> DriftReport:
    """Return a new DriftReport containing only entries that match *f*."""
    filtered = [e for e in report.entries if _entry_matches(e, f)]
    return DriftReport(entries=filtered)


def drift_filter_from_dict(d: dict) -> DriftFilter:
    return DriftFilter(
        kinds=d.get("kinds", []),
        providers=d.get("providers", []),
        resource_ids=d.get("resource_ids", []),
        resource_id_prefix=d.get("resource_id_prefix"),
    )
