"""Weights drift entries by change frequency across history."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from driftwatch.differ import DriftReport, DriftEntry
from driftwatch.history import load as load_history


@dataclass
class FrequencyScore:
    resource_id: str
    kind: str
    provider: str
    drift_count: int
    change_rate: float  # drift_count / total_runs

    def to_dict(self) -> dict:
        return {
            "resource_id": self.resource_id,
            "kind": self.kind,
            "provider": self.provider,
            "drift_count": self.drift_count,
            "change_rate": round(self.change_rate, 4),
        }


@dataclass
class FrequencyReport:
    scores: List[FrequencyScore] = field(default_factory=list)
    total_runs: int = 0

    def to_dict(self) -> dict:
        return {
            "total_runs": self.total_runs,
            "scores": [s.to_dict() for s in self.scores],
        }


def score_by_frequency(config_path: str | None = None) -> FrequencyReport:
    """Analyse history and return per-resource drift frequency scores."""
    entries = load_history(config_path)
    if not entries:
        return FrequencyReport()

    total_runs = len(entries)
    counts: Dict[tuple, int] = {}

    for entry in entries:
        report = entry.get("report", {})
        for drift_entry in report.get("entries", []):
            key = (
                drift_entry.get("resource_id", ""),
                drift_entry.get("kind", ""),
                drift_entry.get("provider", ""),
            )
            counts[key] = counts.get(key, 0) + 1

    scores = [
        FrequencyScore(
            resource_id=k[0],
            kind=k[1],
            provider=k[2],
            drift_count=v,
            change_rate=v / total_runs,
        )
        for k, v in sorted(counts.items(), key=lambda x: -x[1])
    ]

    return FrequencyReport(scores=scores, total_runs=total_runs)
