"""Hook: apply cascade rules during a diff/apply run."""
from __future__ import annotations

from typing import Dict, List

import click

from vaultpatch.cascade import CascadeResult, CascadeRule, build_cascade


def run_cascade(
    source_path: str,
    source_secrets: Dict[str, str],
    rules: List[CascadeRule],
) -> CascadeResult:
    """Execute cascade logic and return the result."""
    return build_cascade(source_path, source_secrets, rules)


def echo_cascade_results(result: CascadeResult) -> None:
    """Print a human-readable summary of cascade propagations and violations."""
    if result.total_propagations == 0 and not result.has_violations:
        click.echo("  cascade: no propagations")
        return

    for target, kv in result.propagations.items():
        keys = ", ".join(sorted(kv.keys()))
        click.echo(f"  cascade -> {target}: [{keys}]")

    for v in result.violations:
        click.echo(f"  cascade warning: {v}", err=True)


def abort_on_cascade_failure(result: CascadeResult) -> None:
    """Raise SystemExit if any cascade violations were recorded."""
    if result.has_violations:
        click.echo(
            f"Cascade check failed: {len(result.violations)} violation(s).",
            err=True,
        )
        raise SystemExit(1)
