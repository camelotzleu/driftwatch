"""CLI commands for managing drift snooze rules."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone

from driftwatch import baseline, differ_snoozer
from driftwatch.collectors import get_collector
from driftwatch.config import load as load_config
from driftwatch.differ import DriftReport


def _load_report(args: argparse.Namespace) -> DriftReport | None:
    cfg = load_config()
    collector = get_collector(cfg.provider)
    if collector is None:
        print(f"Unknown provider: {cfg.provider}")
        return None
    snap = collector.collect(cfg.provider_config)
    base = baseline.load()
    if base is None:
        print("No baseline found. Run 'driftwatch baseline save' first.")
        return None
    from driftwatch.differ import diff
    return diff(base, snap)


def cmd_snooze_add(args: argparse.Namespace) -> int:
    hours = getattr(args, "hours", 24)
    until = (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()
    rules = differ_snoozer.load_rules()
    rules.append(
        differ_snoozer.SnoozeRule(
            resource_id=args.resource_id,
            until=until,
            reason=getattr(args, "reason", ""),
            kind=getattr(args, "kind", None),
            provider=getattr(args, "provider", None),
        )
    )
    differ_snoozer.save_rules(rules)
    print(f"Snoozed '{args.resource_id}' until {until}")
    return 0


def cmd_snooze_show(args: argparse.Namespace) -> int:
    rules = differ_snoozer.load_rules()
    active = [r for r in rules if not r.is_expired()]
    if not active:
        print("No active snooze rules.")
        return 0
    for r in active:
        print(f"  {r.resource_id}  until={r.until}  reason={r.reason or '-'}")
    return 0


def cmd_snooze_clear(args: argparse.Namespace) -> int:
    differ_snoozer.save_rules([])
    print("All snooze rules cleared.")
    return 0


def cmd_snooze_apply(args: argparse.Namespace) -> int:
    report = _load_report(args)
    if report is None:
        return 1
    rules = differ_snoozer.load_rules()
    result = differ_snoozer.snooze_report(report, rules)
    fmt = getattr(args, "format", "text")
    if fmt == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"Active drift entries : {len(result.active)}")
        print(f"Snoozed entries      : {len(result.snoozed)}")
        for e in result.snoozed:
            print(f"  [snoozed] {e.resource_id} ({e.kind})")
    return 1 if result.active else 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("snooze", help="Manage drift snooze rules")
    sub = p.add_subparsers(dest="snooze_cmd")

    add_p = sub.add_parser("add", help="Add a snooze rule")
    add_p.add_argument("resource_id")
    add_p.add_argument("--hours", type=int, default=24)
    add_p.add_argument("--reason", default="")
    add_p.add_argument("--kind", default=None)
    add_p.add_argument("--provider", default=None)
    add_p.set_defaults(func=cmd_snooze_add)

    show_p = sub.add_parser("show", help="Show active snooze rules")
    show_p.set_defaults(func=cmd_snooze_show)

    clear_p = sub.add_parser("clear", help="Clear all snooze rules")
    clear_p.set_defaults(func=cmd_snooze_clear)

    apply_p = sub.add_parser("apply", help="Apply snooze rules to current drift")
    apply_p.add_argument("--format", choices=["text", "json"], default="text")
    apply_p.set_defaults(func=cmd_snooze_apply)
