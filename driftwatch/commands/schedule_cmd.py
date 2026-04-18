"""CLI command: driftwatch schedule — run continuous drift monitoring."""
import argparse
import logging

from driftwatch.config import load as load_config
from driftwatch.scheduler import run_scheduler

logger = logging.getLogger(__name__)


def cmd_schedule(args: argparse.Namespace) -> None:
    """Entry point for the `schedule` sub-command."""
    cfg = load_config(args.config)
    interval = args.interval
    fmt = args.format

    def _on_drift(report):
        if args.fail_on_drift:
            # Signal will be raised after current iteration; just log here.
            logger.warning("Drift detected: %s", report.summary())

    try:
        run_scheduler(cfg, interval=interval, fmt=fmt, on_drift=_on_drift)
    except KeyboardInterrupt:
        print("\nScheduler stopped.")


def register(subparsers) -> None:
    """Register the schedule sub-command with an argparse subparsers action."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "schedule",
        help="Run continuous drift checks at a fixed interval.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        metavar="SECONDS",
        help="Seconds between drift checks (default: 300).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for drift reports.",
    )
    parser.add_argument(
        "--config",
        default="driftwatch.yaml",
        help="Path to configuration file.",
    )
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        default=False,
        help="Log a warning when drift is detected.",
    )
    parser.set_defaults(func=cmd_schedule)
