"""Embargo hook: wire embargo checks into the CLI pipeline."""
from __future__ import annotations

import sys
from typing import List, Optional
from datetime import datetime

import click

from vaultpatch.embargo import EmbargoConfig, EmbargoResult, check_embargo


def run_embargo_check(
    paths: List[str],
    config: EmbargoConfig,
    now: Optional[datetime] = None,
) -> EmbargoResult:
    """Run embargo check and return the result."""
    return check_embargo(paths, config, now=now)


def echo_embargo_results(result: EmbargoResult) -> None:
    """Print embargo check results to stdout/stderr."""
    if not result.has_violations:
        click.echo("embargo: no active embargoes matched")
        return
    for v in result.violations:
        click.echo(str(v), err=True)


def abort_on_embargo(result: EmbargoResult) -> None:
    """Raise SystemExit if any embargo violations were found."""
    if result.has_violations:
        click.echo(
            f"Aborting: {len(result.violations)} embargo violation(s) detected.",
            err=True,
        )
        sys.exit(1)
