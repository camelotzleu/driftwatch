"""Impact assessment for drift entries.

Assigns an impact level and estimated blast radius to each drift entry
based on resource kind, change type, and which attributes changed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from driftwatch.differ import DriftEntry, DriftReport

# Attributes considered high-impact when changed
_HIGH_IMPACT_KEYS = frozenset({
    "instance_type",
    "machine_type",
    "vm_size",
    "image_id",
    "ami",
    "security_groups",
    "iam_instance_profile",
    "subnet_id",
    "network_interfaces",
    "disk_size_gb",
    "os_disk",
    "tags",
})

# Resource kinds that are considered critical infrastructure
_CRITICAL_KINDS = frozenset({
    "ec2_instance",
    "gcp_instance",
    "azure_vm",
    "rds_instance",
    "gke_node",
    "aks_node",
})

_IMPACT_LEVELS = ("low", "medium", "high", "critical")


@dataclass
class ImpactedEntry:
    """A drift entry annotated with impact metadata."""

    entry: DriftEntry
    impact_level: str  # one of: low, medium, high, critical
    impact_score: int  # numeric score used for sorting (higher = more impactful)
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "resource_id": self.entry.resource_id,
            "kind": self.entry.kind,
            "provider": self.entry.provider,
            "change_type": self.entry.change_type,
            "impact_level": self.impact_level,
            "impact_score": self.impact_score,
            "reasons": self.reasons,
        }


@dataclass
class ImpactReport:
    """Collection of impacted entries with aggregate statistics."""

    entries: List[ImpactedEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        counts: dict = {level: 0 for level in _IMPACT_LEVELS}
        for ie in self.entries:
            counts[ie.impact_level] += 1
        return {
            "total": len(self.entries),
            "by_level": counts,
            "entries": [ie.to_dict() for ie in self.entries],
        }


def _assess_entry(entry: DriftEntry) -> ImpactedEntry:
    """Compute impact level and score for a single drift entry."""
    score = 0
    reasons: List[str] = []

    # Change-type weighting
    if entry.change_type in ("added", "removed"):
        score += 30
        reasons.append(f"resource was {entry.change_type}")
    else:
        score += 10

    # Critical resource kind bonus
    if entry.kind in _CRITICAL_KINDS:
        score += 20
        reasons.append(f"kind '{entry.kind}' is critical infrastructure")

    # High-impact attribute changes
    if entry.attribute_diff:
        for key in entry.attribute_diff:
            if key in _HIGH_IMPACT_KEYS:
                score += 15
                reasons.append(f"high-impact attribute changed: '{key}'")

    # Derive level from score
    if score >= 60:
        level = "critical"
    elif score >= 40:
        level = "high"
    elif score >= 20:
        level = "medium"
    else:
        level = "low"

    return ImpactedEntry(
        entry=entry,
        impact_level=level,
        impact_score=score,
        reasons=reasons,
    )


def assess_impact(
    report: DriftReport,
    min_level: Optional[str] = None,
) -> ImpactReport:
    """Assess the impact of every entry in *report*.

    Args:
        report:    The drift report to process.
        min_level: If provided, only entries at or above this level are
                   included (one of 'low', 'medium', 'high', 'critical').

    Returns:
        An :class:`ImpactReport` with entries sorted by descending score.
    """
    min_idx = _IMPACT_LEVELS.index(min_level) if min_level in _IMPACT_LEVELS else 0

    impacted: List[ImpactedEntry] = []
    for entry in report.entries:
        ie = _assess_entry(entry)
        if _IMPACT_LEVELS.index(ie.impact_level) >= min_idx:
            impacted.append(ie)

    impacted.sort(key=lambda ie: ie.impact_score, reverse=True)
    return ImpactReport(entries=impacted)
