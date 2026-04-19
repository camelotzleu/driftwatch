"""CLI commands for audit log management."""
from __future__ import annotations

import argparse
import json

from driftwatch import auditor


def cmd_audit_show(args: argparse.Namespace) -> int:
    entries = auditor.load(config_dir=args.config_dir)
    if not entries:
        print("No audit entries found.")
        return 0

    if getattr(args, "format", "text") == "json":
        print(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        print(f"{'Timestamp':<35} {'Provider':<10} {'Added':>6} {'Removed':>8} {'Changed':>8} {'Drift':>6}")
        print("-" * 80)
        for e in entries:
            drift_flag = "YES" if e.has_drift else "no"
            print(f"{e.timestamp:<35} {e.provider:<10} {e.added:>6} {e.removed:>8} {e.changed:>8} {drift_flag:>6}")
        print(f"\nTotal entries: {len(entries)}")
    return 0


def cmd_audit_clear(args: argparse.Namespace) -> int:
    auditor.clear(config_dir=args.config_dir)
    print("Audit log cleared.")
    return 0


def register(subparsers: argparse._SubParsersAction, parent: argparse.ArgumentParser) -> None:
    audit_p = subparsers.add_parser("audit", help="Manage audit log", parents=[parent])
    audit_sub = audit_p.add_subparsers(dest="audit_cmd")

    show_p = audit_sub.add_parser("show", help="Show audit log entries", parents=[parent])
    show_p.add_argument("--format", choices=["text", "json"], default="text")
    show_p.set_defaults(func=cmd_audit_show)

    clear_p = audit_sub.add_parser("clear", help="Clear audit log", parents=[parent])
    clear_p.set_defaults(func=cmd_audit_clear)
