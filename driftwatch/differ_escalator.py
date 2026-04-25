"""Drift escalation: promote drift entries to higher severity when they
persist across multiple consecutive history runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from driftwatch.differ import DriftReport, DriftEntry
from driftwatch.history import load as load_history


HIGH_IMPACT_KEYS = {"instance_type", "machine_type", "vm_size", "image_id", "ami"}


@dataclass
class EscalatedEntry:
    entry: DriftEntry
    consecutive_runs: int
    escalated: bool
    escalation_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "resource_id": self.entry.resource_id,
            "kind": self.entry.kind,
            "provider": self.entry.provider,
            "change_type": self.entry.change_type,
            "consecutive_runs": self.consecutive_runs,
            "escalated": self.escalated,
            "escalation_reason": self.escalation_reason,
        }


@dataclass
class EscalationReport:
    entries: List[EscalatedEntry] = field(default_factory=list)
    threshold: int = 3

    def to_dict(self) -> dict:
        return {
            "threshold": self.threshold,
            "total": len(self.entries),
            "escalated_count": sum(1 for e in self.entries if e.escalated),
            "entries": [e.to_dict() for e in self.entries],
        }


def _count_consecutive(resource_id: str, kind: str, history: list) -> int:
    """Count how many of the most-recent history runs contain this resource."""
    count = 0
    for run in reversed(history):
        entries = run.get("entries", [])
        ids = {e.get("resource_id") for e in entries if e.get("kind") == kind}
        if resource_id in ids:
            count += 1
        else:
            break
    return count


def escalate_report(
    report: DriftReport,
    threshold: int = 3,
    history_path: Optional[str] = None,
) -> EscalationReport:
    """Evaluate each drift entry and escalate those that persist >= threshold runs."""
    history = load_history(path=history_path) if history_path else load_history()
    raw_history = [h if isinstance(h, dict) else h.to_dict() for h in (history or [])]

    result = EscalationReport(threshold=threshold)
    for entry in report.entries:
        consecutive = _count_consecutive(entry.resource_id, entry.kind, raw_history)
        escalated = consecutive >= threshold
        reason = ""
        if escalated:
            reason = f"Persisted for {consecutive} consecutive run(s) (threshold={threshold})"
        elif entry.change_type in ("added", "removed"):
            reason = "High-impact change type"
            escalated = True
        result.entries.append(
            EscalatedEntry(
                entry=entry,
                consecutive_runs=consecutive,
                escalated=escalated,
                escalation_reason=reason,
            )
        )
    return result
