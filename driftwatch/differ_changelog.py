"""Changelog builder: produces a human-readable change log from drift history."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from driftwatch.history import load as load_history


@dataclass
class ChangelogEntry:
    run_id: str
    timestamp: str
    provider: str
    resource_id: str
    kind: str
    change_type: str  # added | removed | changed
    summary: str

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "provider": self.provider,
            "resource_id": self.resource_id,
            "kind": self.kind,
            "change_type": self.change_type,
            "summary": self.summary,
        }


@dataclass
class ChangelogReport:
    entries: List[ChangelogEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"entries": [e.to_dict() for e in self.entries]}

    def to_text(self) -> str:
        if not self.entries:
            return "No changes recorded."
        lines = []
        for e in self.entries:
            lines.append(
                f"[{e.timestamp}] ({e.run_id}) {e.change_type.upper()} "
                f"{e.provider}/{e.kind}/{e.resource_id} — {e.summary}"
            )
        return "\n".join(lines)


def _summary_for(entry: dict) -> str:
    change_type = entry.get("change_type", "changed")
    if change_type == "added":
        return "Resource appeared in snapshot."
    if change_type == "removed":
        return "Resource disappeared from snapshot."
    attr_diff = entry.get("attribute_diff", {})
    if attr_diff:
        keys = ", ".join(sorted(attr_diff.keys()))
        return f"Attributes changed: {keys}"
    return "Drift detected."


def build_changelog(
    limit: Optional[int] = None,
    provider_filter: Optional[str] = None,
) -> ChangelogReport:
    """Build a ChangelogReport from persisted drift history."""
    history = load_history()
    report = ChangelogReport()

    for run in history:
        run_id = run.get("run_id", "unknown")
        timestamp = run.get("timestamp", "")
        drift = run.get("drift", {})
        for entry in drift.get("entries", []):
            provider = entry.get("provider", "unknown")
            if provider_filter and provider != provider_filter:
                continue
            report.entries.append(
                ChangelogEntry(
                    run_id=run_id,
                    timestamp=timestamp,
                    provider=provider,
                    resource_id=entry.get("resource_id", ""),
                    kind=entry.get("kind", ""),
                    change_type=entry.get("change_type", "changed"),
                    summary=_summary_for(entry),
                )
            )

    if limit is not None:
        report.entries = report.entries[-limit:]
    return report
