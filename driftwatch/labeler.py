"""Labeler: attach computed labels to drift entries based on rules."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from driftwatch.differ import DriftEntry, DriftReport


@dataclass
class LabelRule:
    label: str
    kind: str | None = None
    provider: str | None = None
    attribute_contains: str | None = None


@dataclass
class LabeledEntry:
    entry: DriftEntry
    labels: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = {
            "resource_id": self.entry.resource_id,
            "kind": self.entry.kind,
            "provider": self.entry.provider,
            "change_type": self.entry.change_type,
            "labels": self.labels,
        }
        if self.entry.attribute_diff:
            d["attribute_diff"] = self.entry.attribute_diff
        return d


def _entry_matches_rule(entry: DriftEntry, rule: LabelRule) -> bool:
    if rule.kind and entry.kind != rule.kind:
        return False
    if rule.provider and entry.provider != rule.provider:
        return False
    if rule.attribute_contains and entry.attribute_diff:
        keys = entry.attribute_diff.keys()
        if not any(rule.attribute_contains in k for k in keys):
            return False
    elif rule.attribute_contains and not entry.attribute_diff:
        return False
    return True


def label_entry(entry: DriftEntry, rules: list[LabelRule]) -> LabeledEntry:
    labels = [r.label for r in rules if _entry_matches_rule(entry, r)]
    return LabeledEntry(entry=entry, labels=labels)


def label_report(report: DriftReport, rules: list[LabelRule]) -> list[LabeledEntry]:
    return [label_entry(e, rules) for e in report.entries]


def label_rules_from_list(raw: list[dict[str, Any]]) -> list[LabelRule]:
    return [
        LabelRule(
            label=r["label"],
            kind=r.get("kind"),
            provider=r.get("provider"),
            attribute_contains=r.get("attribute_contains"),
        )
        for r in raw
    ]
