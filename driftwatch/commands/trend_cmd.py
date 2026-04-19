"""CLI command: driftwatch trend — show drift trend analysis."""
from __future__ import annotations

import argparse
import json

from driftwatch.differ_trend import analyze_trend


def cmd_trend(args: argparse.Namespace) -> int:
    report = analyze_trend(windows=args.windows)

    if not report.entries:
        print("No history data available for trend analysis.")
        return 0

    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
        return 0

    # text output
    print(f"Drift Trend Analysis ({args.windows} windows)")
    print("-" * 50)
    rising = [e for e in report.entries if e.trend == "rising"]
    stable = [e for e in report.entries if e.trend == "stable"]
    falling = [e for e in report.entries if e.trend == "falling"]

    for label, group in (("RISING", rising), ("STABLE", stable), ("FALLING", falling)):
        if not group:
            continue
        print(f"\n{label}:")
        for e in group:
            counts_str = " -> ".join(str(c) for c in e.drift_counts)
            print(f"  {e.resource_id} [{e.kind}/{e.provider}]  {counts_str}")

    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("trend", help="Analyze drift frequency trends across history windows")
    p.add_argument(
        "--windows",
        type=int,
        default=3,
        help="Number of time windows to split history into (default: 3)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    p.set_defaults(func=cmd_trend)
