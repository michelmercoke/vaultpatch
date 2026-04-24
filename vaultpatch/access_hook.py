"""CLI-level helpers that wire AccessResult into the vaultpatch workflow."""
from __future__ import annotations

import sys
from typing import List

import click

from vaultpatch.access import AccessResult, AccessRule, check_access


def run_access_check(
    namespace: str,
    paths: List[str],
    rules: List[AccessRule],
    default_allow: bool = True,
) -> AccessResult:
    """Run access check and return the result (no side-effects)."""
    return check_access(namespace, paths, rules, default_allow=default_allow)


def echo_access_results(result: AccessResult) -> None:
    """Print a human-readable summary of access violations to stdout."""
    if result.allowed:
        click.echo("Access check passed — all paths permitted.")
        return
    click.echo(f"Access check failed — {len(result.violations)} violation(s):")
    for v in result.violations:
        click.echo(f"  DENIED  {v}", err=False)


def abort_on_access_denied(result: AccessResult) -> None:
    """Exit with code 1 if any access violation was found."""
    if not result.allowed:
        click.echo(
            f"Aborting: {len(result.violations)} access violation(s) detected.",
            err=True,
        )
        sys.exit(1)
