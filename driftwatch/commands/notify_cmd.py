"""CLI sub-command: notify — send drift report to configured webhook."""
from __future__ import annotations

import argparse
import sys

from driftwatch.baseline import load as load_baseline
from driftwatch.collectors import get_collector
from driftwatch.config import load as load_config
from driftwatch.differ import compare
from driftwatch.notifier import NotifierConfig, send_webhook
from driftwatch.reporter import render


def _resolve_webhook_url(args: argparse.Namespace, cfg) -> str | None:
    """Return the webhook URL from CLI args or config, preferring CLI arg."""
    if args.webhook:
        return args.webhook
    if cfg.notify and cfg.notify.webhook_url:
        return cfg.notify.webhook_url
    return None


def cmd_notify(args: argparse.Namespace) -> int:
    """Run the notify sub-command.

    Collects current state, compares it against the saved baseline, renders
    the drift report, and — when drift is detected — posts a notification to
    the configured webhook URL.

    Returns:
        0  — success (no drift, or notification sent).
        1  — configuration / baseline error.
        2  — webhook delivery failure.
    """
    cfg = load_config(args.config)
    baseline = load_baseline(cfg)
    if baseline is None:
        print("No baseline found. Run 'driftwatch baseline save' first.", file=sys.stderr)
        return 1

    collector = get_collector(cfg)
    current = collector.collect()
    report = compare(baseline, current)

    print(render(report, fmt=args.format))

    if not report.has_drift():
        print("No drift detected — nothing to notify.")
        return 0

    webhook_url = _resolve_webhook_url(args, cfg)
    if not webhook_url:
        print("No webhook URL configured. Use --webhook or set notify.webhook_url in config.", file=sys.stderr)
        return 1

    ncfg = NotifierConfig(webhook_url=webhook_url)
    ok = send_webhook(report, ncfg.webhook_url)
    if ok:
        print("Notification sent successfully.")
    else:
        print("Failed to send notification.", file=sys.stderr)
        return 2
    return 0


def register(subparsers) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("notify", help="Send drift alert to a webhook")
    p.add_argument("--webhook", metavar="URL", help="Slack-compatible webhook URL")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--config", default="driftwatch.yaml")
    p.set_defaults(func=cmd_notify)
