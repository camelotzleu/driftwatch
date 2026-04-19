"""Enriches drift entries with additional metadata (labels, severity hints, context)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from driftwatch.differ import DriftEntry, DriftReport


@dataclass
class EnrichedEntry:
    entry: DriftEntry
    labels: Dict[str, str] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "resource_id": self.entry.resource_id,
            "kind": self.entry.kind,
            "provider": self.entry.provider,
            "change_type": self.entry.change_type,
            "labels": self.labels,
            "notes": self.notes,
        }
        if self.entry.attribute_diff:
            d["attribute_diff"] = self.entry.attribute_diff
        return d


@dataclass
class EnrichmentRule:
    match_kind: Optional[str] = None
    match_provider: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    note: Optional[str] = None

    def matches(self, entry: DriftEntry) -> bool:
        if self.match_kind and entry.kind != self.match_kind:
            return False
        if self.match_provider and entry.provider != self.match_provider:
            return False
        return True


def enrich_entry(entry: DriftEntry, rules: List[EnrichmentRule]) -> EnrichedEntry:
    enriched = EnrichedEntry(entry=entry)
    for rule in rules:
        if rule.matches(entry):
            enriched.labels.update(rule.labels)
            if rule.note:
                enriched.notes.append(rule.note)
    return enriched


def enrich_report(
    report: DriftReport, rules: List[EnrichmentRule]
) -> List[EnrichedEntry]:
    return [enrich_entry(e, rules) for e in report.entries]


def rules_from_config(raw: List[dict]) -> List[EnrichmentRule]:
    rules = []
    for item in raw:
        rules.append(
            EnrichmentRule(
                match_kind=item.get("kind"),
                match_provider=item.get("provider"),
                labels=item.get("labels", {}),
                note=item.get("note"),
            )
        )
    return rules
