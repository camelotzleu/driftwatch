"""CLI command for exporting drift reports to JSON or CSV."""
from __future__ import annotations

import argparse
import sys

from driftwatch import baseline, config, exporter
from driftwatch.collectors import get_collector
from driftwatch.differ import DriftReport, compare


def cmd_export(args: argparse.Namespace) -> int:
    cfg = config.load(args.config)
    provider_cfg = cfg.providers.get(args.provider)
    if provider_cfg is None:
        print(f"[error] provider '{args.provider}' not found in config", file=sys.stderr)
        return 1

    collector = get_collector(provider_cfg)
    current = collector.collect()

    base = baseline.load(args.provider)
    if base is None:
        print(f"[error] no baseline found for provider '{args.provider}'", file=sys.stderr)
        return 1

    from driftwatch.differ import compare as diff_compare
    report: DriftReport = diff_compare(base, current)

    fmt = args.format.lower()
    output = exporter.export(report, fmt)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(f"[ok] exported {fmt} report to {args.output}")
    else:
        print(output)

    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("export", help="Export drift report to JSON or CSV")
    p.add_argument("provider", help="Provider name defined in config")
    p.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Output format (default: json)",
    )
    p.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write output to FILE instead of stdout",
    )
    p.add_argument(
        "--config",
        default="driftwatch.yaml",
        help="Path to config file (default: driftwatch.yaml)",
    )
    p.set_defaults(func=cmd_export)
