"""CLI command: group drift entries by a dimension."""
from __future__ import annotations
import argparse
import json
import sys

from driftwatch import baseline, collector_runner
from driftwatch.config import load as load_config
from driftwatch.differ import compare
from driftwatch.differ_grouper import group_report, GroupBy
from driftwatch.collectors import get_collector


def cmd_group(args: argparse.Namespace) -> int:
    cfg = load_config()
    provider_cfg = cfg.providers.get(args.provider)
    if provider_cfg is None:
        print(f"Unknown provider: {args.provider}", file=sys.stderr)
        return 1

    snap = get_collector(provider_cfg).collect()

    base = baseline.load(args.provider)
    if base is None:
        print("No baseline found. Run 'driftwatch baseline save' first.", file=sys.stderr)
        return 1

    report = compare(base, snap)
    if not report.has_drift():
        print("No drift detected.")
        return 0

    group_by: GroupBy = args.group_by  # type: ignore[assignment]
    grp = group_report(report, group_by=group_by)

    if args.format == "json":
        print(json.dumps(grp.to_dict(), indent=2))
    else:
        for key, g in grp.groups.items():
            print(f"[{key}] {g.count} entries")
            for e in g.entries:
                print(f"  {e.change_type:8s}  {e.resource_id}  ({e.kind})")
    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("group", help="Group drift entries by a dimension")
    p.add_argument("provider", help="Provider name")
    p.add_argument(
        "--group-by",
        dest="group_by",
        choices=["provider", "kind", "change_type"],
        default="kind",
    )
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_group)
