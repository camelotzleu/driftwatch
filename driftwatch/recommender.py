"""Drift remediation recommender: suggests actions based on drift entries."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from driftwatch.differ import DriftReport, DriftEntry


@dataclass
class Recommendation:
    resource_id: str
    provider: str
    kind: str
    change_type: str  # added | removed | changed
    action: str
    detail: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "resource_id": self.resource_id,
            "provider": self.provider,
            "kind": self.kind,
            "change_type": self.change_type,
            "action": self.action,
            "detail": self.detail,
        }


@dataclass
class RecommendationReport:
    recommendations: List[Recommendation] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"recommendations": [r.to_dict() for r in self.recommendations]}


def _recommend_for_entry(entry: DriftEntry) -> Recommendation:
    if entry.change_type == "added":
        action = "Review and baseline new resource if intentional; remove if unexpected."
        detail = None
    elif entry.change_type == "removed":
        action = "Restore resource from backup or re-provision if removal was unintended."
        detail = None
    else:
        changed_keys = list((entry.attribute_diff or {}).keys())
        detail = f"Changed attributes: {', '.join(changed_keys)}" if changed_keys else None
        action = "Reconcile configuration to match baseline or update baseline to reflect intent."
    return Recommendation(
        resource_id=entry.resource_id,
        provider=entry.provider,
        kind=entry.kind,
        change_type=entry.change_type,
        action=action,
        detail=detail,
    )


def recommend(report: DriftReport) -> RecommendationReport:
    """Generate remediation recommendations for all drift entries."""
    recs = [_recommend_for_entry(e) for e in report.entries]
    return RecommendationReport(recommendations=recs)
