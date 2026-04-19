"""Alerting rules: suppress or escalate drift based on severity thresholds."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from driftwatch.differ import DriftReport, DriftEntry


@dataclass
class AlertRule:
    name: str
    min_changes: int = 1
    resource_types: List[str] = field(default_factory=list)
    providers: List[str] = field(default_factory=list)
    severity: str = "warning"  # info | warning | critical


@dataclass
class AlertResult:
    rule: AlertRule
    matched_entries: List[DriftEntry]

    @property
    def severity(self) -> str:
        return self.rule.severity

    @property
    def triggered(self) -> bool:
        return len(self.matched_entries) >= self.rule.min_changes


def _entry_matches_rule(entry: DriftEntry, rule: AlertRule) -> bool:
    if rule.resource_types and entry.resource_type not in rule.resource_types:
        return False
    if rule.providers and entry.provider not in rule.providers:
        return False
    return True


def evaluate(report: DriftReport, rules: List[AlertRule]) -> List[AlertResult]:
    """Evaluate all rules against a drift report."""
    results = []
    for rule in rules:
        matched = [e for e in report.entries if _entry_matches_rule(e, rule)]
        results.append(AlertResult(rule=rule, matched_entries=matched))
    return results


def rules_from_dict(data: list) -> List[AlertRule]:
    rules = []
    for item in data:
        rules.append(AlertRule(
            name=item["name"],
            min_changes=item.get("min_changes", 1),
            resource_types=item.get("resource_types", []),
            providers=item.get("providers", []),
            severity=item.get("severity", "warning"),
        ))
    return rules
