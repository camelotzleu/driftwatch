"""CLI command: compare two saved baseline files."""
from __future__ import annotations
import argparse
import json
import sys
from driftwatch.baseline import load as load_baseline
from driftwatch.differ_baseline_diff import diff_baselines


def cmd_baseline_diff(args: argparse.Namespace) -> int:
    old_snap = load_baseline(args.old)
    if old_snap is None:
        print(f"[error] baseline not found: {args.old}", file=sys.stderr)
        return 1

    new_snap = load_baseline(args.new)
    if new_snap is None:
        print(f"[error] baseline not found: {args.new}", file=sys.stderr)
        return 1

    report = diff_baselines(old_snap, new_snap)

    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
        return 0

    summary = report.summary()
    print(f"Baseline diff: {summary['added']} added, {summary['removed']} removed, {summary['changed']} changed")
    if not report.has_changes:
        print("No changes between baselines.")
        return 0

    for e in report.entries:
        tag = e.change.upper().ljust(8)
        print(f"  [{tag}] {e.provider}/{e.kind}/{e.resource_id}")
        if e.old_fingerprint:
            print(f"           old: {e.old_fingerprint}")
        if e.new_fingerprint:
            print(f"           new: {e.new_fingerprint}")
    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("baseline-diff", help="Compare two baseline snapshots")
    p.add_argument("old", help="Path to the older baseline JSON file")
    p.add_argument("new", help="Path to the newer baseline JSON file")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_baseline_diff)
