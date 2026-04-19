"""CLI command: compare current state against the saved baseline."""
from __future__ import annotations

import argparse
import sys

from driftwatch.collectors import get_collector
from driftwatch.comparator import compare_to_baseline
from driftwatch.config import load as load_config
from driftwatch.reporter import render


def cmd_compare(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    collector = get_collector(cfg.provider)
    current = collector.collect(cfg.provider)

    result = compare_to_baseline(current, config_dir=args.baseline_dir)

    if result.baseline_missing:
        print("[driftwatch] No baseline found. Run 'driftwatch baseline save' first.",
              file=sys.stderr)
        return 1

    if result.error:
        print(f"[driftwatch] Comparison error: {result.error}", file=sys.stderr)
        return 2

    report = result.report
    fmt = getattr(args, "format", "text")
    print(render(report, fmt=fmt))
    return 0 if not report.has_drift() else 3


def register(subparsers) -> None:
    p = subparsers.add_parser("compare",
                              help="Compare live state against saved baseline")
    p.add_argument("--config", default="driftwatch.yaml",
                   help="Path to config file")
    p.add_argument("--baseline-dir", default=".",
                   help="Directory containing the baseline file")
    p.add_argument("--format", choices=["text", "json"], default="text",
                   help="Output format")
    p.set_defaults(func=cmd_compare)
