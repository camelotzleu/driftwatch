"""CLI command for validating drift reports."""
import json
import argparse
from driftwatch.config import load as load_config
from driftwatch.collectors import get_collector
from driftwatch.baseline import load as load_baseline
from driftwatch.differ import DriftReport
from driftwatch.comparator import compare_snapshots
from driftwatch.differ_validator import validate_report, validation_rules_from_dict


def cmd_validate(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    provider_cfg = next((p for p in cfg.providers if p.name == args.provider), None)
    if provider_cfg is None:
        print(f"Unknown provider: {args.provider}")
        return 1

    baseline = load_baseline(args.provider)
    if baseline is None:
        print("No baseline found. Run 'driftwatch baseline save' first.")
        return 1

    collector = get_collector(provider_cfg)
    current = collector.collect()
    drift_report = compare_snapshots(baseline, current)

    rules_data = {"validation_rules": args.rules_json and json.loads(args.rules_json) or []}
    rules = validation_rules_from_dict(rules_data)
    if not rules:
        print("No validation rules provided.")
        return 1

    result = validate_report(drift_report, rules)

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        if result.valid:
            print("Validation passed: no violations found.")
        else:
            print(f"Validation failed: {result.violation_count} violation(s)")
            for v in result.violations:
                msg = f"  [{v.rule.field}] {v.entry.resource_id}: got '{v.actual_value}', allowed {v.rule.allowed_values}"
                if v.rule.message:
                    msg += f" — {v.rule.message}"
                print(msg)

    return 0 if result.valid else 2


def register(subparsers):
    p = subparsers.add_parser("validate", help="Validate drift report entries against rules")
    p.add_argument("--provider", required=True)
    p.add_argument("--config", default="driftwatch.yaml")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--rules-json", dest="rules_json", default=None,
                   help='JSON array of rules, e.g. [{"field":"kind","allowed_values":["instance"]}]')
    p.set_defaults(func=cmd_validate)
