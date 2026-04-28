"""Drift budget tracking: enforce a maximum number of drift entries per run."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from driftwatch.differ import DriftReport, DriftEntry


@dataclass
class BudgetResult:
    entry: DriftEntry
    within_budget: bool
    position: int  # 1-based rank in this run

    def to_dict(self) -> dict:
        return {
            "resource_id": self.entry.resource_id,
            "kind": self.entry.kind,
            "provider": self.entry.provider,
            "change_type": self.entry.change_type,
            "within_budget": self.within_budget,
            "position": self.position,
        }


@dataclass
class BudgetReport:
    limit: int
    total_entries: int
    accepted: List[BudgetResult] = field(default_factory=list)
    rejected: List[BudgetResult] = field(default_factory=list)

    @property
    def over_budget(self) -> bool:
        return self.total_entries > self.limit

    @property
    def budget_used(self) -> int:
        return len(self.accepted)

    def to_dict(self) -> dict:
        return {
            "limit": self.limit,
            "total_entries": self.total_entries,
            "budget_used": self.budget_used,
            "over_budget": self.over_budget,
            "accepted": [r.to_dict() for r in self.accepted],
            "rejected": [r.to_dict() for r in self.rejected],
        }


def apply_budget(
    report: DriftReport,
    limit: int,
    priority_change_types: Optional[List[str]] = None,
) -> BudgetReport:
    """Apply a drift budget, accepting at most *limit* entries.

    Entries whose change_type appears in *priority_change_types* are ranked
    first (in the order they appear in the report); remaining entries follow.
    """
    if priority_change_types is None:
        priority_change_types = ["removed", "added"]

    all_entries = list(report.entries)
    priority = [e for e in all_entries if e.change_type in priority_change_types]
    rest = [e for e in all_entries if e.change_type not in priority_change_types]
    ordered = priority + rest

    accepted: List[BudgetResult] = []
    rejected: List[BudgetResult] = []

    for pos, entry in enumerate(ordered, start=1):
        within = pos <= limit
        result = BudgetResult(entry=entry, within_budget=within, position=pos)
        if within:
            accepted.append(result)
        else:
            rejected.append(result)

    return BudgetReport(
        limit=limit,
        total_entries=len(ordered),
        accepted=accepted,
        rejected=rejected,
    )
