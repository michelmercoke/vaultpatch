"""Hook helpers for scope enforcement within the CLI pipeline."""
from __future__ import annotations

import sys
from typing import List

import click

from vaultpatch.scope import ScopeConfig, ScopeResult, check_scope


def run_scope_check(
    config: ScopeConfig,
    namespace: str,
    paths: List[str],
) -> ScopeResult:
    """Run scope check and return the result."""
    return check_scope(config, namespace, paths)


def echo_scope_results(result: ScopeResult) -> None:
    """Print scope violations to stderr; print OK message if none."""
    if not result.has_violations:
        click.echo("scope: all paths within permitted scope")
        return
    for v in result.violations:
        click.echo(f"scope violation: {v}", err=True)


def abort_on_scope_violation(result: ScopeResult) -> None:
    """Raise SystemExit if there are any scope violations."""
    if result.has_violations:
        click.echo(
            f"Aborting: {len(result.violations)} scope violation(s) detected.",
            err=True,
        )
        sys.exit(1)
