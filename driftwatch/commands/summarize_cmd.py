"""CLI sub-command: summarize — print a drift digest for the current baseline vs live state."""
from __future__ import annotations
import argparse
import sys
from driftwatch.config import load as load_config
from driftwatch.baseline import load as load_baseline
from driftwatch.collectors import get_collector
from driftwatch.differ import compare
from driftwatch.summarizer import summarize, format_digest


def cmd_summarize(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)

    baseline = load_baseline(cfg)
    if baseline is None:
        print("No baseline found. Run 'driftwatch baseline save' first.", file=sys.stderr)
        return 1

    collector = get_collector(cfg.provider)
    current = collector.collect()

    report = compare(baseline, current)
    summary = summarize(report)

    if args.format == "json":
        import json
        print(json.dumps(summary.to_dict(), indent=2))
    else:
        print(format_digest(summary))

    return 0 if not report.has_drift() else 2


def register(subparsers) -> None:
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "summarize",
        help="Print a short drift digest comparing baseline to live state.",
    )
    parser.add_argument(
        "--config",
        default="driftwatch.yaml",
        metavar="FILE",
        help="Path to configuration file (default: driftwatch.yaml).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json.",
    )
    parser.set_defaults(func=cmd_summarize)
