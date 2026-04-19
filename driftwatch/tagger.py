"""Tag-based filtering for drift reports."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from driftwatch.differ import DriftReport, DriftEntry


@dataclass
class TagFilter:
    required: Dict[str, str] = field(default_factory=dict)
    excluded: Dict[str, str] = field(default_factory=dict)


def _entry_matches(entry: DriftEntry, tag_filter: TagFilter) -> bool:
    tags = entry.attributes_after or entry.attributes_before or {}
    resource_tags = tags.get("tags", {})
    if not isinstance(resource_tags, dict):
        resource_tags = {}

    for key, value in tag_filter.required.items():
        if resource_tags.get(key) != value:
            return False

    for key, value in tag_filter.excluded.items():
        if resource_tags.get(key) == value:
            return False

    return True


def filter_report(report: DriftReport, tag_filter: TagFilter) -> DriftReport:
    """Return a new DriftReport containing only entries matching the tag filter."""
    filtered: List[DriftEntry] = [
        e for e in report.entries if _entry_matches(e, tag_filter)
    ]
    return DriftReport(entries=filtered)


def tag_filter_from_dict(data: dict) -> TagFilter:
    return TagFilter(
        required=data.get("required", {}),
        excluded=data.get("excluded", {}),
    )


def apply_tag_filter_if_configured(
    report: DriftReport, config_tags: Optional[dict]
) -> DriftReport:
    if not config_tags:
        return report
    tf = tag_filter_from_dict(config_tags)
    return filter_report(report, tf)
