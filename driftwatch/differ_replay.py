"""differ_replay.py — replay historical drift runs and reconstruct a timeline.

Allows users to replay a sequence of history entries to understand how
configuration drift evolved over time across resources and providers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from driftwatch.history import load as load_history


@dataclass
class ReplayFrame:
    """A single point-in-time snapshot of drift state during replay."""

    run_index: int
    timestamp: str
    provider: str
    resource_id: str
    kind: str
    change_type: str  # added | removed | changed
    attribute_diff: Dict[str, object]
    cumulative_changes: int  # total changes for this resource up to this frame

    def to_dict(self) -> Dict[str, object]:
        return {
            "run_index": self.run_index,
            "timestamp": self.timestamp,
            "provider": self.provider,
            "resource_id": self.resource_id,
            "kind": self.kind,
            "change_type": self.change_type,
            "attribute_diff": self.attribute_diff,
            "cumulative_changes": self.cumulative_changes,
        }


@dataclass
class ReplayReport:
    """Full replay timeline built from history entries."""

    frames: List[ReplayFrame] = field(default_factory=list)
    total_runs_replayed: int = 0
    resource_ids_seen: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "total_runs_replayed": self.total_runs_replayed,
            "resource_ids_seen": self.resource_ids_seen,
            "frames": [f.to_dict() for f in self.frames],
        }

    def to_text(self) -> str:
        if not self.frames:
            return "No drift frames to replay."
        lines = [
            f"Replay: {self.total_runs_replayed} run(s), "
            f"{len(self.resource_ids_seen)} unique resource(s)",
            "-" * 60,
        ]
        for fr in self.frames:
            diff_str = ", ".join(
                f"{k}: {v}" for k, v in fr.attribute_diff.items()
            ) if fr.attribute_diff else "—"
            lines.append(
                f"[{fr.run_index:>3}] {fr.timestamp[:19]}  "
                f"{fr.provider}/{fr.kind}/{fr.resource_id}  "
                f"({fr.change_type})  cumulative={fr.cumulative_changes}  "
                f"diff=[{diff_str}]"
            )
        return "\n".join(lines)


def replay_history(
    history_file: Optional[str] = None,
    provider_filter: Optional[str] = None,
    resource_id_filter: Optional[str] = None,
    max_runs: Optional[int] = None,
) -> ReplayReport:
    """Replay drift history and return a structured timeline.

    Args:
        history_file: Path to the JSONL history file (uses default if None).
        provider_filter: Only include frames for this provider.
        resource_id_filter: Only include frames for this resource ID.
        max_runs: Cap the number of history runs to replay.

    Returns:
        A ReplayReport with ordered ReplayFrame objects.
    """
    entries = load_history(history_file) if history_file else load_history()
    if max_runs is not None:
        entries = entries[:max_runs]

    frames: List[ReplayFrame] = []
    # Track cumulative change count per resource
    cumulative: Dict[str, int] = {}
    seen_ids: List[str] = []

    for run_index, entry in enumerate(entries):
        timestamp = entry.get("timestamp", "")
        drift_entries = entry.get("report", {}).get("entries", [])

        for de in drift_entries:
            provider = de.get("provider", "unknown")
            resource_id = de.get("resource_id", "unknown")
            kind = de.get("kind", "unknown")
            change_type = de.get("change_type", "changed")
            attribute_diff = de.get("attribute_diff", {})

            if provider_filter and provider != provider_filter:
                continue
            if resource_id_filter and resource_id != resource_id_filter:
                continue

            key = f"{provider}/{resource_id}"
            cumulative[key] = cumulative.get(key, 0) + 1

            if resource_id not in seen_ids:
                seen_ids.append(resource_id)

            frames.append(
                ReplayFrame(
                    run_index=run_index,
                    timestamp=timestamp,
                    provider=provider,
                    resource_id=resource_id,
                    kind=kind,
                    change_type=change_type,
                    attribute_diff=attribute_diff,
                    cumulative_changes=cumulative[key],
                )
            )

    return ReplayReport(
        frames=frames,
        total_runs_replayed=len(entries),
        resource_ids_seen=seen_ids,
    )
