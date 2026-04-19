"""Rank drift entries by impact score and frequency."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from driftwatch.differ import DriftReport, DriftEntry

_KIND_WEIGHT = {"added": 3, "removed": 3, "changed": 1}
_HIGH_IMPACT_KEYS = {"instance_type", "machine_type", "vm_size", "image_id", "region"}


@dataclass
class RankedEntry:
    entry: DriftEntry
    score: float

    def to_dict(self) -> dict:
        d = {
            "resource_id": self.entry.resource_id,
            "kind": self.entry.kind,
            "provider": self.entry.provider,
            "change_type": self.entry.change_type,
            "score": self.score,
        }
        if self.entry.attribute_diff:
            d["attribute_diff"] = self.entry.attribute_diff
        return d


@dataclass
class RankReport:
    ranked: List[RankedEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"ranked": [r.to_dict() for r in self.ranked]}


def _score_entry(entry: DriftEntry) -> float:
    base = float(_KIND_WEIGHT.get(entry.change_type, 1))
    if entry.attribute_diff:
        for key in entry.attribute_diff:
            if key in _HIGH_IMPACT_KEYS:
                base += 2.0
        base += len(entry.attribute_diff) * 0.5
    return round(base, 2)


def rank_report(report: DriftReport, top_n: int = 0) -> RankReport:
    ranked = sorted(
        [RankedEntry(entry=e, score=_score_entry(e)) for e in report.entries],
        key=lambda r: r.score,
        reverse=True,
    )
    if top_n > 0:
        ranked = ranked[:top_n]
    return RankReport(ranked=ranked)
