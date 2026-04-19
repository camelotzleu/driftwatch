"""Annotate drift entries with contextual notes based on rules."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from driftwatch.differ import DriftEntry, DriftReport


@dataclass
class AnnotationRule:
    note: str
    kind: Optional[str] = None
    provider: Optional[str] = None
    change_type: Optional[str] = None  # added | removed | changed

    def matches(self, entry: DriftEntry) -> bool:
        if self.kind and entry.kind != self.kind:
            return False
        if self.provider and entry.provider != self.provider:
            return False
        if self.change_type and entry.change_type != self.change_type:
            return False
        return True


@dataclass
class AnnotatedEntry:
    entry: DriftEntry
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "resource_id": self.entry.resource_id,
            "kind": self.entry.kind,
            "provider": self.entry.provider,
            "change_type": self.entry.change_type,
            "notes": self.notes,
        }
        if self.entry.attribute_diff:
            d["attribute_diff"] = self.entry.attribute_diff
        return d


@dataclass
class AnnotationReport:
    entries: List[AnnotatedEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"annotated_entries": [e.to_dict() for e in self.entries]}


def annotate_report(report: DriftReport, rules: List[AnnotationRule]) -> AnnotationReport:
    result = []
    for entry in report.entries:
        notes = [r.note for r in rules if r.matches(entry)]
        result.append(AnnotatedEntry(entry=entry, notes=notes))
    return AnnotationReport(entries=result)
