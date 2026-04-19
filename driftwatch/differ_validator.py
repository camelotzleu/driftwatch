"""Validates drift report entries against configurable rules."""
from dataclasses import dataclass, field
from typing import List, Optional
from driftwatch.differ import DriftReport, DriftEntry


@dataclass
class ValidationRule:
    field: str  # 'kind', 'provider', 'change_type'
    allowed_values: List[str]
    message: Optional[str] = None


@dataclass
class ValidationViolation:
    entry: DriftEntry
    rule: ValidationRule
    actual_value: str

    def to_dict(self) -> dict:
        return {
            "resource_id": self.entry.resource_id,
            "kind": self.entry.kind,
            "provider": self.entry.provider,
            "field": self.rule.field,
            "allowed": self.rule.allowed_values,
            "actual": self.actual_value,
            "message": self.rule.message,
        }


@dataclass
class ValidationReport:
    violations: List[ValidationViolation] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return len(self.violations) == 0

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "violation_count": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
        }


def _get_field_value(entry: DriftEntry, field_name: str) -> Optional[str]:
    return getattr(entry, field_name, None)


def validate_report(report: DriftReport, rules: List[ValidationRule]) -> ValidationReport:
    violations: List[ValidationViolation] = []
    for entry in report.entries:
        for rule in rules:
            value = _get_field_value(entry, rule.field)
            if value is not None and value not in rule.allowed_values:
                violations.append(ValidationViolation(entry=entry, rule=rule, actual_value=value))
    return ValidationReport(violations=violations)


def validation_rules_from_dict(data: dict) -> List[ValidationRule]:
    rules = []
    for item in data.get("validation_rules", []):
        rules.append(ValidationRule(
            field=item["field"],
            allowed_values=item["allowed_values"],
            message=item.get("message"),
        ))
    return rules
