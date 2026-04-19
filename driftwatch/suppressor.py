"""Suppression rules: silence known/expected drift entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from driftwatch.differ import DriftEntry, DriftReport


@dataclass
class SuppressionRule:
    resource_id: Optional[str] = None
    kind: Optional[str] = None
    provider: Optional[str] = None
    reason: str = "suppressed"


@dataclass
class SuppressionResult:
    kept: List[DriftEntry] = field(default_factory=list)
    suppressed: List[DriftEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "kept": len(self.kept),
            "suppressed": len(self.suppressed),
            "suppressed_ids": [e.resource_id for e in self.suppressed],
        }


def _entry_matches_rule(entry: DriftEntry, rule: SuppressionRule) -> bool:
    if rule.resource_id and entry.resource_id != rule.resource_id:
        return False
    if rule.kind and entry.kind != rule.kind:
        return False
    if rule.provider and entry.provider != rule.provider:
        return False
    return True


def suppress_report(
    report: DriftReport, rules: List[SuppressionRule]
) -> SuppressionResult:
    result = SuppressionResult()
    for entry in report.entries:
        matched = any(_entry_matches_rule(entry, r) for r in rules)
        if matched:
            result.suppressed.append(entry)
        else:
            result.kept.append(entry)
    return result


def suppression_rules_from_dict(data: List[dict]) -> List[SuppressionRule]:
    rules = []
    for item in data:
        rules.append(
            SuppressionRule(
                resource_id=item.get("resource_id"),
                kind=item.get("kind"),
                provider=item.get("provider"),
                reason=item.get("reason", "suppressed"),
            )
        )
    return rules
