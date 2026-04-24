"""CLI command: silence — apply silence rules to a drift report."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from driftwatch.collectors import get_collector
from driftwatch.comparator import compare_to_baseline
from driftwatch.config import load as load_config
from driftwatch.differ_silencer import SilenceRule, rules_from_list, silence_report


def _rules_from_config(cfg) -> List[SilenceRule]:
    raw = getattr(cfg, "silence_rules", None) or []
    if isinstance(raw, list):
        return rules_from_list(raw)
    return []


def cmd_silence(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)

    provider_cfg = next(
        (p for p in cfg.providers if p.name == args.provider), None
    )
    if provider_cfg is None:
        print(f"[error] unknown provider: {args.provider}", file=sys.stderr)
        return 1

    collector = get_collector(provider_cfg)
    snapshot = collector.collect()
    result = compare_to_baseline(snapshot, provider_cfg.name)
    if not result.ok:
        print("[warn] no baseline found — nothing to silence.", file=sys.stderr)
        return 1

    rules: List[SilenceRule] = []
    if args.rules_file:
        try:
            with open(args.rules_file) as fh:
                raw = json.load(fh)
            rules = rules_from_list(raw if isinstance(raw, list) else raw.get("rules", []))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[error] could not load rules file: {exc}", file=sys.stderr)
            return 1
    else:
        rules = _rules_from_config(cfg)

    silence_result = silence_report(result.report, rules)

    if args.format == "json":
        print(json.dumps(silence_result.to_dict(), indent=2))
    else:
        print(f"Active entries  : {len(silence_result.active)}")
        print(f"Silenced entries: {len(silence_result.silenced)}")
        print(f"Rules applied   : {silence_result.rules_applied}")
        for e in silence_result.silenced:
            print(f"  [silenced] {e.provider}/{e.kind}/{e.resource_id}")

    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("silence", help="Mute drift entries matching silence rules")
    p.add_argument("provider", help="Provider name")
    p.add_argument("--rules-file", dest="rules_file", default=None,
                   help="JSON file containing silence rules")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--config", default="driftwatch.yaml")
    p.set_defaults(func=cmd_silence)
