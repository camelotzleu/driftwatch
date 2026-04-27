"""CLI command: driftwatch changelog — show a human-readable drift changelog."""
from __future__ import annotations

import argparse
import json
import sys

from driftwatch.differ_changelog import build_changelog


def cmd_changelog(args: argparse.Namespace) -> int:
    provider = getattr(args, "provider", None) or None
    limit = getattr(args, "limit", None)
    fmt = getattr(args, "format", "text")

    report = build_changelog(limit=limit, provider_filter=provider)

    if fmt == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(report.to_text())

    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "changelog",
        help="Show a human-readable changelog of all recorded drift events.",
    )
    p.add_argument(
        "--provider",
        default=None,
        help="Filter changelog to a specific provider (e.g. aws, gcp, azure).",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Show only the last N changelog entries.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.set_defaults(func=cmd_changelog)
