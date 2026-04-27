"""Drift heatmap: counts drift events per resource over history runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from driftwatch.history import load as load_history


@dataclass
class HeatmapCell:
    resource_id: str
    kind: str
    provider: str
    drift_count: int
    run_count: int

    def to_dict(self) -> dict:
        return {
            "resource_id": self.resource_id,
            "kind": self.kind,
            "provider": self.provider,
            "drift_count": self.drift_count,
            "run_count": self.run_count,
            "heat": self.heat,
        }

    @property
    def heat(self) -> float:
        """Fraction of runs in which this resource drifted."""
        if self.run_count == 0:
            return 0.0
        return round(self.drift_count / self.run_count, 4)


@dataclass
class HeatmapReport:
    cells: List[HeatmapCell] = field(default_factory=list)
    total_runs: int = 0

    def to_dict(self) -> dict:
        return {
            "total_runs": self.total_runs,
            "cells": [c.to_dict() for c in sorted(
                self.cells, key=lambda c: c.heat, reverse=True
            )],
        }


def build_heatmap(history_file: str | None = None) -> HeatmapReport:
    """Build a heatmap from the drift history log."""
    entries = load_history(history_file)
    if not entries:
        return HeatmapReport()

    # key -> (drift_count, run_count, kind, provider)
    counts: Dict[str, list] = {}
    total_runs = len(entries)

    for entry in entries:
        report = entry.get("report", {})
        drift_entries = report.get("entries", [])
        seen_in_run: set = set()
        for e in drift_entries:
            rid = e.get("resource_id", "")
            kind = e.get("kind", "")
            provider = e.get("provider", "")
            key = f"{provider}::{kind}::{rid}"
            if key not in counts:
                counts[key] = [0, 0, kind, provider, rid]
            if key not in seen_in_run:
                counts[key][0] += 1
                seen_in_run.add(key)

    cells = []
    for key, (drift_count, _, kind, provider, rid) in counts.items():
        cells.append(HeatmapCell(
            resource_id=rid,
            kind=kind,
            provider=provider,
            drift_count=drift_count,
            run_count=total_runs,
        ))

    return HeatmapReport(cells=cells, total_runs=total_runs)
