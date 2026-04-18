"""CLI sub-commands for drift history."""
from __future__ import annotations

import argparse
import json
import sys

import driftwatch.history as history_mod


def cmd_history_show(args: argparse.Namespace) -> int:
    entries = history_mod.load(limit=args.limit)
    if not entries:
        print("No drift history found.")
        return 0
    if args.format == "json":
        print(json.dumps(entries, indent=2))
    else:
        for e in entries:
            drift_flag = "[DRIFT]" if e.get("has_drift") else "[clean]"
            print(f"{e['timestamp']}  {drift_flag}  {e['summary']}")
    return 0


def cmd_history_clear(args: argparse.Namespace) -> int:
    history_mod.clear()
    print("Drift history cleared.")
    return 0


def register(subparsers) -> None:
    hist_parser = subparsers.add_parser("history", help="Manage drift history log")
    hist_sub = hist_parser.add_subparsers(dest="history_cmd")

    show_p = hist_sub.add_parser("show", help="Display recent drift history")
    show_p.add_argument(
        "--limit", type=int, default=20, help="Max entries to display (default: 20)"
    )
    show_p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    show_p.set_defaults(func=cmd_history_show)

    clear_p = hist_sub.add_parser("clear", help="Delete the history log")
    clear_p.set_defaults(func=cmd_history_clear)
