"""Helper to ensure validate_cmd is registered in register_all.

This module is imported by commands/__init__.py via register_all.
It exists to isolate the registration concern and keep __init__.py clean.

Usage in driftwatch/commands/__init__.py:
    from driftwatch.commands import validate_cmd
    validate_cmd.register(subparsers)
"""
# This file is intentionally minimal — registration is done in __init__.py.
# Keeping it here documents the integration point for the validate feature.

from driftwatch.commands.validate_cmd import register as register_validate  # noqa: F401
