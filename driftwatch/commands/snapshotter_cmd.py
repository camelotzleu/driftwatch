"""CLI commands for labeled snapshot store comparisons."""
from __future__ import annotations

import argparse
import json
import sys

from driftwatch.collector_runner import collect_snapshot
from driftwatch.config import load as load_config
from driftwatch.differ_snapshotter import SnapshotStore, compare_labeled
from driftwatch.reporter import render

# Module-level store shared across sub-commands within a session.
_store = SnapshotStore()


def cmd_snapshotter(args: argparse.Namespace) -> int:
    cfg = load_config(getattr(args, "config", None))

    if args.sub == "capture":
        snap = collect_snapshot(cfg, args.provider)
        if snap is None:
            print(f"Unknown provider: {args.provider}", file=sys.stderr)
            return 1
        _store.put(args.label, snap)
        print(f"Captured snapshot '{args.label}' for provider '{args.provider}'.")
        return 0

    if args.sub == "list":
        labels = _store.labels()
        if not labels:
            print("No snapshots in store.")
        else:
            for lbl in labels:
                print(f"  {lbl}")
        return 0

    if args.sub == "compare":
        try:
            result = compare_labeled(_store, args.old, args.new)
        except KeyError as exc:
            print(str(exc), file=sys.stderr)
            return 1

        if getattr(args, "format", "text") == "json":
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(render(result.report, fmt="text"))
        return 0 if result.ok else 2

    if args.sub == "drop":
        removed = _store.remove(args.label)
        if removed:
            print(f"Dropped snapshot '{args.label}'.")
        else:
            print(f"Snapshot '{args.label}' not found.", file=sys.stderr)
            return 1
        return 0

    print(f"Unknown sub-command: {args.sub}", file=sys.stderr)
    return 1


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("snapshotter", help="Labeled in-memory snapshot store")
    sub = p.add_subparsers(dest="sub", required=True)

    cap = sub.add_parser("capture", help="Capture a snapshot under a label")
    cap.add_argument("label", help="Label for the snapshot")
    cap.add_argument("provider", help="Provider to collect from")

    sub.add_parser("list", help="List stored snapshot labels")

    cmp = sub.add_parser("compare", help="Compare two labeled snapshots")
    cmp.add_argument("old", help="Old snapshot label")
    cmp.add_argument("new", help="New snapshot label")
    cmp.add_argument("--format", choices=["text", "json"], default="text")

    drop = sub.add_parser("drop", help="Remove a snapshot from the store")
    drop.add_argument("label", help="Label to remove")

    p.set_defaults(func=cmd_snapshotter)
