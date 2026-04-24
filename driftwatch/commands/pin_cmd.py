"""CLI commands for managing pinned (acknowledged) drift entries."""
from __future__ import annotations

import argparse
import json
import sys

from driftwatch import baseline, differ
from driftwatch.collectors import get_collector
from driftwatch.config import load as load_config
from driftwatch.differ_pinner import (
    PinnedEntry,
    load_pins,
    pin_report,
    save_pins,
)


def cmd_pin(args: argparse.Namespace) -> int:
    cfg = load_config()
    provider_cfg = next(
        (p for p in cfg.providers if p.name == args.provider), None
    )
    if provider_cfg is None:
        print(f"Unknown provider: {args.provider}", file=sys.stderr)
        return 1

    snap = get_collector(provider_cfg).collect()
    base = baseline.load(args.provider)
    if base is None:
        print("No baseline found. Run 'baseline save' first.", file=sys.stderr)
        return 1

    report = differ.compare(base, snap)
    pins = load_pins()

    # Pin entries matching given resource_ids (or all if --all)
    newly_pinned: list[PinnedEntry] = []
    for entry in report.entries:
        if args.all or entry.resource_id in (args.resource_ids or []):
            pe = PinnedEntry(
                resource_id=entry.resource_id,
                kind=entry.kind,
                provider=entry.provider,
                reason=args.reason or "",
            )
            if pe not in pins:
                pins.append(pe)
                newly_pinned.append(pe)

    save_pins(pins)
    print(f"Pinned {len(newly_pinned)} entries.")
    return 0


def cmd_pin_show(args: argparse.Namespace) -> int:
    pins = load_pins()
    if not pins:
        print("No pinned entries.")
        return 0
    if getattr(args, "format", "text") == "json":
        print(json.dumps([p.to_dict() for p in pins], indent=2))
    else:
        for p in pins:
            reason = f" ({p.reason})" if p.reason else ""
            print(f"  [{p.provider}] {p.kind}/{p.resource_id}{reason}")
    return 0


def cmd_pin_clear(args: argparse.Namespace) -> int:
    save_pins([])
    print("Cleared all pinned entries.")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("pin", help="Pin (acknowledge) drift entries")
    sub = p.add_subparsers(dest="pin_cmd")

    add_p = sub.add_parser("add", help="Pin entries from a provider's current drift")
    add_p.add_argument("provider")
    add_p.add_argument("resource_ids", nargs="*")
    add_p.add_argument("--all", action="store_true", help="Pin all drifted resources")
    add_p.add_argument("--reason", default="", help="Reason for pinning")
    add_p.set_defaults(func=cmd_pin)

    show_p = sub.add_parser("show", help="Show pinned entries")
    show_p.add_argument("--format", choices=["text", "json"], default="text")
    show_p.set_defaults(func=cmd_pin_show)

    clear_p = sub.add_parser("clear", help="Clear all pinned entries")
    clear_p.set_defaults(func=cmd_pin_clear)
