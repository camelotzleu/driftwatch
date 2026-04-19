"""Baseline diff: compare two baselines and produce a change summary."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from driftwatch.snapshot import Snapshot


@dataclass
class BaselineDiffEntry:
    resource_id: str
    provider: str
    kind: str
    change: str  # "added" | "removed" | "changed"
    old_fingerprint: str | None = None
    new_fingerprint: str | None = None

    def to_dict(self) -> dict:
        return {
            "resource_id": self.resource_id,
            "provider": self.provider,
            "kind": self.kind,
            "change": self.change,
            "old_fingerprint": self.old_fingerprint,
            "new_fingerprint": self.new_fingerprint,
        }


@dataclass
class BaselineDiffReport:
    entries: List[BaselineDiffEntry] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.entries) > 0

    def summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {"added": 0, "removed": 0, "changed": 0}
        for e in self.entries:
            counts[e.change] = counts.get(e.change, 0) + 1
        return counts

    def to_dict(self) -> dict:
        return {
            "has_changes": self.has_changes,
            "summary": self.summary(),
            "entries": [e.to_dict() for e in self.entries],
        }


def diff_baselines(old: Snapshot, new: Snapshot) -> BaselineDiffReport:
    """Compare two snapshots and return a BaselineDiffReport."""
    old_map = {r.resource_id: r for r in old.resources}
    new_map = {r.resource_id: r for r in new.resources}
    entries: List[BaselineDiffEntry] = []

    for rid, res in new_map.items():
        if rid not in old_map:
            entries.append(BaselineDiffEntry(
                resource_id=rid, provider=res.provider, kind=res.kind,
                change="added", new_fingerprint=res.fingerprint,
            ))
        elif res.fingerprint != old_map[rid].fingerprint:
            entries.append(BaselineDiffEntry(
                resource_id=rid, provider=res.provider, kind=res.kind,
                change="changed",
                old_fingerprint=old_map[rid].fingerprint,
                new_fingerprint=res.fingerprint,
            ))

    for rid, res in old_map.items():
        if rid not in new_map:
            entries.append(BaselineDiffEntry(
                resource_id=rid, provider=res.provider, kind=res.kind,
                change="removed", old_fingerprint=res.fingerprint,
            ))

    return BaselineDiffReport(entries=entries)
