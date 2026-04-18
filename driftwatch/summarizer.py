"""Summarize drift reports into human-readable or structured digests."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from driftwatch.differ import DriftReport, DriftEntry


@dataclass
class DriftSummary:
    total: int = 0
    added: int = 0
    removed: int = 0
    changed: int = 0
    providers: List[str] = field(default_factory=list)
    top_changes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "added": self.added,
            "removed": self.removed,
            "changed": self.changed,
            "providers": self.providers,
            "top_changes": self.top_changes,
        }


def _collect_providers(entries: List[DriftEntry]) -> List[str]:
    seen = []
    for e in entries:
        p = e.resource_id.split(":")[0] if ":" in e.resource_id else "unknown"
        if p not in seen:
            seen.append(p)
    return seen


def _top_changed_resources(entries: List[DriftEntry], n: int = 5) -> List[str]:
    changed = [e.resource_id for e in entries if e.change_type == "changed"]
    return changed[:n]


def summarize(report: DriftReport) -> DriftSummary:
    """Produce a DriftSummary from a DriftReport."""
    entries = report.entries
    summary = DriftSummary(
        total=len(entries),
        added=sum(1 for e in entries if e.change_type == "added"),
        removed=sum(1 for e in entries if e.change_type == "removed"),
        changed=sum(1 for e in entries if e.change_type == "changed"),
        providers=_collect_providers(entries),
        top_changes=_top_changed_resources(entries),
    )
    return summary


def format_digest(summary: DriftSummary) -> str:
    """Return a short plain-text digest string."""
    lines = [
        f"Drift digest: {summary.total} resource(s) affected",
        f"  Added:   {summary.added}",
        f"  Removed: {summary.removed}",
        f"  Changed: {summary.changed}",
    ]
    if summary.providers:
        lines.append(f"  Providers: {', '.join(summary.providers)}")
    if summary.top_changes:
        lines.append("  Top changed resources:")
        for r in summary.top_changes:
            lines.append(f"    - {r}")
    return "\n".join(lines)
