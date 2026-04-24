"""Ignore rules for suppressing specific drift entries from reports."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from driftwatch.differ import DriftEntry, DriftReport


@dataclass
class IgnoreRule:
    resource_id: Optional[str] = None
    kind: Optional[str] = None
    provider: Optional[str] = None
    reason: str = ""

    def matches(self, entry: DriftEntry) -> bool:
        if self.resource_id and entry.resource_id != self.resource_id:
            return False
        if self.kind and entry.kind != self.kind:
            return False
        if self.provider and entry.provider != self.provider:
            return False
        return True


@dataclass
class IgnoreResult:
    kept: List[DriftEntry] = field(default_factory=list)
    ignored: List[DriftEntry] = field(default_factory=list)
    ignored_reasons: dict = field(default_factory=dict)  # resource_id -> reason

    def to_dict(self) -> dict:
        return {
            "kept_count": len(self.kept),
            "ignored_count": len(self.ignored),
            "ignored": [
                {
                    "resource_id": e.resource_id,
                    "kind": e.kind,
                    "provider": e.provider,
                    "change_type": e.change_type,
                    "reason": self.ignored_reasons.get(e.resource_id, ""),
                }
                for e in self.ignored
            ],
        }


def ignore_report(report: DriftReport, rules: List[IgnoreRule]) -> IgnoreResult:
    """Apply ignore rules to a drift report, returning kept and ignored entries."""
    result = IgnoreResult()
    for entry in report.entries:
        matched_rule = None
        for rule in rules:
            if rule.matches(entry):
                matched_rule = rule
                break
        if matched_rule:
            result.ignored.append(entry)
            result.ignored_reasons[entry.resource_id] = matched_rule.reason
        else:
            result.kept.append(entry)
    return result


def ignore_rules_from_list(raw: List[dict]) -> List[IgnoreRule]:
    """Deserialise a list of raw dicts into IgnoreRule objects."""
    rules = []
    for item in raw:
        rules.append(
            IgnoreRule(
                resource_id=item.get("resource_id"),
                kind=item.get("kind"),
                provider=item.get("provider"),
                reason=item.get("reason", ""),
            )
        )
    return rules
