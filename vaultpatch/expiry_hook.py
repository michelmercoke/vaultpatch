"""CLI integration hook for expiry checks."""
from __future__ import annotations

import sys
from typing import Dict, List

import click

from vaultpatch.expiry import ExpiryResult, check_expiry, summarise_expiry


def run_expiry_check(
    path_secrets: Dict[str, Dict[str, str]],
    warn_days: int = 14,
) -> List[ExpiryResult]:
    """Run expiry checks over a mapping of {path: secrets}."""
    results = []
    for path, secrets in path_secrets.items():
        results.append(check_expiry(path, secrets, warn_days=warn_days))
    return results


def echo_expiry_results(results: List[ExpiryResult]) -> None:
    """Print warnings and violations to stdout/stderr."""
    for result in results:
        for warning in result.warnings:
            click.echo(f"[WARN]  {warning}")
        for violation in result.violations:
            click.echo(f"[EXPIRED] {violation}", err=True)

    click.echo(summarise_expiry(results))


def abort_on_expiry(results: List[ExpiryResult]) -> None:
    """Exit with code 1 if any expiry violations are present."""
    if any(r.has_violations for r in results):
        click.echo("Aborting: one or more secrets have expired.", err=True)
        sys.exit(1)
