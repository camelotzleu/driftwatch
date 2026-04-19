"""CLI command: report drift frequency scores from history."""
from __future__ import annotations

import argparse
import json

from driftwatch.differ_scorer import score_by_frequency


def cmd_frequency(args: argparse.Namespace) -> int:
    report = score_by_frequency(getattr(args, "config", None))

    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
        return 0

    if not report.scores:
        print("No drift history found.")
        return 0

    print(f"Drift frequency report ({report.total_runs} run(s) analysed)")
    print(f"{'Resource ID':<36} {'Kind':<16} {'Provider':<10} {'Drifts':>6} {'Rate':>8}")
    print("-" * 82)
    for s in report.scores:
        print(
            f"{s.resource_id:<36} {s.kind:<16} {s.provider:<10}"
            f" {s.drift_count:>6} {s.change_rate:>8.2%}"
        )
    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "frequency",
        help="Show drift frequency scores derived from run history",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_frequency)
