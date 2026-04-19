"""Drift severity scoring based on report entries."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from driftwatch.differ import DriftReport, DriftEntry

# Weight per change kind
_KIND_WEIGHTS = {
    "added": 1,
    "removed": 2,
    "changed": 1,
}

# Bonus weight when many attributes changed on a single resource
_ATTR_CHANGE_MULTIPLIER = 0.5


@dataclass
class ScoredEntry:
    entry: DriftEntry
    score: float

    def to_dict(self) -> dict:
        d = {
            "resource_id": self.entry.resource_id,
            "kind": self.entry.kind,
            "provider": self.entry.provider,
            "score": round(self.score, 3),
        }
        if self.entry.attribute_diff:
            d["changed_attributes"] = len(self.entry.attribute_diff)
        return d


@dataclass
class ScoreReport:
    entries: List[ScoredEntry] = field(default_factory=list)
    total_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "total_score": round(self.total_score, 3),
            "entries": [e.to_dict() for e in self.entries],
        }


def _score_entry(entry: DriftEntry) -> float:
    base = _KIND_WEIGHTS.get(entry.kind, 1)
    attr_bonus = 0.0
    if entry.attribute_diff:
        attr_bonus = len(entry.attribute_diff) * _ATTR_CHANGE_MULTIPLIER
    return base + attr_bonus


def score_report(report: DriftReport) -> ScoreReport:
    """Compute a drift score for every entry in *report*."""
    scored: List[ScoredEntry] = []
    for entry in report.entries:
        s = _score_entry(entry)
        scored.append(ScoredEntry(entry=entry, score=s))
    scored.sort(key=lambda e: e.score, reverse=True)
    total = sum(e.score for e in scored)
    return ScoreReport(entries=scored, total_score=total)
