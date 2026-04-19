"""Classify drift entries by impact level based on change patterns."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
from driftwatch.differ import DriftReport, DriftEntry

HIGH_IMPACT_KEYS = {"instance_type", "machine_type", "vm_size", "image", "iam_profile"}
MEDIUM_IMPACT_KEYS = {"tags", "labels", "security_groups", "network"}


@dataclass
class ClassifiedEntry:
    entry: DriftEntry
    impact: str  # "high" | "medium" | "low"

    def to_dict(self) -> Dict:
        d = {
            "resource_id": self.entry.resource_id,
            "kind": self.entry.kind,
            "provider": self.entry.provider,
            "change_type": self.entry.change_type,
            "impact": self.impact,
        }
        if self.entry.attribute_diff:
            d["attribute_diff"] = self.entry.attribute_diff
        return d


@dataclass
class ClassificationReport:
    entries: List[ClassifiedEntry] = field(default_factory=list)

    def to_dict(self) -> Dict:
        counts = {"high": 0, "medium": 0, "low": 0}
        for e in self.entries:
            counts[e.impact] += 1
        return {
            "total": len(self.entries),
            "counts": counts,
            "entries": [e.to_dict() for e in self.entries],
        }


def _classify_entry(entry: DriftEntry) -> str:
    if entry.change_type in ("added", "removed"):
        return "high"
    changed_keys = set((entry.attribute_diff or {}).keys())
    if changed_keys & HIGH_IMPACT_KEYS:
        return "high"
    if changed_keys & MEDIUM_IMPACT_KEYS:
        return "medium"
    return "low"


def classify_report(report: DriftReport) -> ClassificationReport:
    result = ClassificationReport()
    for entry in report.entries:
        impact = _classify_entry(entry)
        result.entries.append(ClassifiedEntry(entry=entry, impact=impact))
    return result
