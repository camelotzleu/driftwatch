"""Group drift entries by a given dimension for reporting."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Literal

from driftwatch.differ import DriftEntry, DriftReport

GroupBy = Literal["provider", "kind", "change_type"]


@dataclass
class DriftGroup:
    key: str
    entries: List[DriftEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "count": len(self.entries),
            "entries": [
                {
                    "resource_id": e.resource_id,
                    "kind": e.kind,
                    "provider": e.provider,
                    "change_type": e.change_type,
                }
                for e in self.entries
            ],
        }


@dataclass
class GroupReport:
    group_by: str
    groups: Dict[str, DriftGroup] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "group_by": self.group_by,
            "groups": {k: v.to_dict() for k, v in self.groups.items()},
        }


def _key_for(entry: DriftEntry, group_by: GroupBy) -> str:
    if group_by == "provider":
        return entry.provider
    if group_by == "kind":
        return entry.kind
    if group_by == "change_type":
        return entry.change_type
    raise ValueError(f"Unknown group_by: {group_by}")


def group_report(report: DriftReport, group_by: GroupBy = "provider") -> GroupReport:
    result = GroupReport(group_by=group_by)
    for entry in report.entries:
        key = _key_for(entry, group_by)
        if key not in result.groups:
            result.groups[key] = DriftGroup(key=key)
        result.groups[key].entries.append(entry)
    return result
