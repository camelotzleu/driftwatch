"""CLI command: aggregate drift reports from history or multiple baselines."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from driftwatch import history
from driftwatch.differ import DriftReport, DriftEntry
from driftwatch.differ_aggregator import aggregate_reports


def _reports_from_history(limit: int) -> tuple[List[DriftReport], List[str]]:
    entries = history.load()
    if not entries:
        return [], []
    entries = entries[-limit:]
    reports = []
    labels = []
    for entry in entries:
        raw = entry.get("report", {})
        drift_entries = [
            DriftEntry(
                resource_id=e["resource_id"],
                kind=e["kind"],
                provider=e["provider"],
                change_type=e["change_type"],
                attribute_diff=e.get("attribute_diff", {}),
            )
            for e in raw.get("entries", [])
        ]
        reports.append(DriftReport(entries=drift_entries))
        labels.append(entry.get("timestamp", f"run_{len(labels)}"))
    return reports, labels


def cmd_aggregate(args: argparse.Namespace) -> int:
    reports, labels = _reports_from_history(args.limit)

    if not reports:
        print("No history entries found.", file=sys.stderr)
        return 1

    result = aggregate_reports(reports, labels)

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        d = result.to_dict()
        print(f"Aggregated {d['total_reports']} reports, {d['total_entries']} unique drift entries.")
        for e in result.entries:
            src = ", ".join(e.sources)
            print(f"  [{e.change_type.upper()}] {e.provider}/{e.kind}/{e.resource_id} "
                  f"(occurrences={e.occurrences}, sources={src})")
    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("aggregate", help="Aggregate drift entries across history runs")
    p.add_argument("--limit", type=int, default=10, help="Number of recent history entries to include")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_aggregate)
