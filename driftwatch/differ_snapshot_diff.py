"""Point-in-time snapshot comparison: diff two named snapshots from history."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from driftwatch.snapshot import Snapshot
from driftwatch.differ import DriftReport, compare


@dataclass
class SnapshotDiffResult:
    old_label: str
    new_label: str
    report: DriftReport
    ok: bool

    def to_dict(self) -> dict:
        return {
            "old_label": self.old_label,
            "new_label": self.new_label,
            "ok": self.ok,
            "drift_count": len(self.report.entries),
            "entries": [
                {
                    "resource_id": e.resource_id,
                    "kind": e.kind,
                    "provider": e.provider,
                    "change_type": e.change_type,
                    "attribute_diff": e.attribute_diff,
                }
                for e in self.report.entries
            ],
        }


def diff_snapshots(
    old_snapshot: Snapshot,
    new_snapshot: Snapshot,
    old_label: str = "old",
    new_label: str = "new",
) -> SnapshotDiffResult:
    """Compare two snapshots and return a SnapshotDiffResult."""
    report = compare(old_snapshot, new_snapshot)
    return SnapshotDiffResult(
        old_label=old_label,
        new_label=new_label,
        report=report,
        ok=not report.has_drift(),
    )
