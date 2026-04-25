"""Snapshot comparison utilities: diff two named snapshots by label."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from driftwatch.differ import DriftReport, compare
from driftwatch.snapshot import Snapshot


@dataclass
class LabeledSnapshot:
    label: str
    snapshot: Snapshot

    def to_dict(self) -> dict:
        return {"label": self.label, "snapshot": self.snapshot.to_dict()}


@dataclass
class SnapshotCompareResult:
    old_label: str
    new_label: str
    report: DriftReport
    ok: bool

    def to_dict(self) -> dict:
        return {
            "old_label": self.old_label,
            "new_label": self.new_label,
            "ok": self.ok,
            "has_drift": self.report.has_drift(),
            "summary": self.report.summary(),
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


@dataclass
class SnapshotStore:
    """In-memory store of labeled snapshots."""
    _store: Dict[str, Snapshot] = field(default_factory=dict)

    def put(self, label: str, snapshot: Snapshot) -> None:
        self._store[label] = snapshot

    def get(self, label: str) -> Optional[Snapshot]:
        return self._store.get(label)

    def labels(self) -> List[str]:
        return list(self._store.keys())

    def remove(self, label: str) -> bool:
        if label in self._store:
            del self._store[label]
            return True
        return False


def compare_labeled(
    store: SnapshotStore,
    old_label: str,
    new_label: str,
) -> SnapshotCompareResult:
    """Compare two snapshots by their labels in the store."""
    old_snap = store.get(old_label)
    new_snap = store.get(new_label)

    if old_snap is None or new_snap is None:
        missing = old_label if old_snap is None else new_label
        raise KeyError(f"Snapshot label not found in store: '{missing}'")

    report = compare(old_snap, new_snap)
    return SnapshotCompareResult(
        old_label=old_label,
        new_label=new_label,
        report=report,
        ok=not report.has_drift(),
    )
