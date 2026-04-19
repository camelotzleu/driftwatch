"""CLI command: annotate drift entries with notes from config rules."""
from __future__ import annotations
import argparse
import json
from driftwatch.config import load as load_config
from driftwatch.collectors import get_collector
from driftwatch.baseline import load as load_baseline
from driftwatch.differ import compare
from driftwatch.differ_annotator import AnnotationRule, annotate_report


def _rules_from_config(cfg) -> list:
    raw = getattr(cfg, "annotation_rules", []) or []
    rules = []
    for r in raw:
        rules.append(AnnotationRule(
            note=r.get("note", ""),
            kind=r.get("kind"),
            provider=r.get("provider"),
            change_type=r.get("change_type"),
        ))
    return rules


def cmd_annotate(args: argparse.Namespace) -> int:
    cfg = load_config()
    collector = get_collector(cfg.provider)
    if collector is None:
        print(f"Unknown provider: {cfg.provider.name}")
        return 1

    baseline = load_baseline(cfg.provider.name)
    if baseline is None:
        print("No baseline found. Run 'driftwatch baseline save' first.")
        return 1

    current = collector.collect()
    report = compare(baseline, current)
    rules = _rules_from_config(cfg)
    annotated = annotate_report(report, rules)

    if args.format == "json":
        print(json.dumps(annotated.to_dict(), indent=2))
    else:
        if not annotated.entries:
            print("No drift entries to annotate.")
        for ae in annotated.entries:
            print(f"[{ae.entry.change_type.upper()}] {ae.entry.resource_id} ({ae.entry.kind}/{ae.entry.provider})")
            for note in ae.notes:
                print(f"  NOTE: {note}")
            if not ae.notes:
                print("  (no annotations)")
    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("annotate", help="Annotate drift entries with config-defined notes")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_annotate)
