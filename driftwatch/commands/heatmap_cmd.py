"""CLI command: driftwatch heatmap — show drift heatmap from history."""
from __future__ import annotations

import argparse
import json
import sys

from driftwatch.differ_heatmap import build_heatmap


def cmd_heatmap(args: argparse.Namespace) -> int:
    report = build_heatmap(getattr(args, "history_file", None))

    if not report.cells:
        print("No drift history found — heatmap is empty.")
        return 0

    fmt = getattr(args, "format", "text")

    if fmt == "json":
        print(json.dumps(report.to_dict(), indent=2))
        return 0

    # text table
    header = f"{'RESOURCE':<40} {'KIND':<18} {'PROVIDER':<12} {'DRIFTS':>6} {'RUNS':>5} {'HEAT':>6}"
    print(header)
    print("-" * len(header))
    for cell in sorted(report.cells, key=lambda c: c.heat, reverse=True):
        print(
            f"{cell.resource_id:<40} {cell.kind:<18} {cell.provider:<12}"
            f" {cell.drift_count:>6} {cell.run_count:>5} {cell.heat:>6.2%}"
        )
    print(f"\nTotal runs analysed: {report.total_runs}")
    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("heatmap", help="Show drift heatmap across history runs")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--history-file",
        dest="history_file",
        default=None,
        help="Path to history JSONL file (default: auto-detected)",
    )
    p.set_defaults(func=cmd_heatmap)
