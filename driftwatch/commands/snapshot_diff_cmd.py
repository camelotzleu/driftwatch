"""CLI command: compare two saved baseline snapshots by file path."""
from __future__ import annotations
import argparse
import json
import sys
from driftwatch import baseline as bl
from driftwatch.differ_snapshot_diff import diff_snapshots
from driftwatch.reporter import render


def cmd_snapshot_diff(args: argparse.Namespace) -> int:
    old_snap = bl.load(args.old)
    if old_snap is None:
        print(f"[error] could not load snapshot from: {args.old}", file=sys.stderr)
        return 1

    new_snap = bl.load(args.new)
    if new_snap is None:
        print(f"[error] could not load snapshot from: {args.new}", file=sys.stderr)
        return 1

    result = diff_snapshots(old_snap, new_snap, old_label=args.old, new_label=args.new)

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"Comparing: {args.old}  →  {args.new}")
        print(render(result.report, fmt="text"))

    return 0 if result.ok else 2


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("snapshot-diff", help="Compare two baseline snapshot files")
    p.add_argument("old", help="Path to the older baseline JSON file")
    p.add_argument("new", help="Path to the newer baseline JSON file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_snapshot_diff)
