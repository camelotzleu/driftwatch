"""Entry-point for the driftwatch CLI."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from driftwatch.config import load
from driftwatch.reporter import OutputFormat, render


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="driftwatch",
        description="Detect and report configuration drift across cloud environments.",
    )
    parser.add_argument(
        "--config",
        metavar="FILE",
        default="driftwatch.yaml",
        help="Path to configuration file (default: driftwatch.yaml)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write report to FILE instead of stdout",
    )

    sub = parser.add_subparsers(dest="command")
    sub.add_parser("report", help="Run drift detection and print report")
    sub.add_parser("version", help="Print version and exit")
    return parser


def cmd_version() -> None:
    from importlib.metadata import version, PackageNotFoundError
    try:
        v = version("driftwatch")
    except PackageNotFoundError:
        v = "dev"
    print(f"driftwatch {v}")


def cmd_report(args: argparse.Namespace) -> int:
    """Stub: load config, run providers, diff snapshots, render report."""
    cfg = load(Path(args.config))
    # TODO: wire up provider collection and snapshot diffing
    from driftwatch.differ import DriftReport
    report = DriftReport(entries=[])

    if args.output:
        with open(args.output, "w") as fh:
            render(report, fmt=args.fmt, out=fh)
    else:
        render(report, fmt=args.fmt)

    return 1 if report.has_drift() else 0


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        cmd_version()
        sys.exit(0)
    else:
        sys.exit(cmd_report(args))


if __name__ == "__main__":
    main()
