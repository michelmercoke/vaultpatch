"""Hook to run schema checks inside the CLI diff/apply flow."""
from __future__ import annotations

from typing import Dict, Optional

import click

from vaultpatch.schema import SchemaConfig, SchemaCheckResult, check_secrets


def run_schema_check(
    secrets: Dict[str, str],
    schema: Optional[SchemaConfig],
) -> Optional[SchemaCheckResult]:
    """Run schema validation if a schema is provided. Returns None when skipped."""
    if schema is None:
        return None
    return check_secrets(secrets, schema)


def echo_schema_results(result: SchemaCheckResult, path: str) -> None:
    """Print schema validation results to the terminal."""
    if result.valid:
        click.echo(click.style(f"  [schema] {path}: OK", fg="green"))
    else:
        click.echo(click.style(f"  [schema] {path}: FAILED", fg="red"))
        for err in result.errors:
            click.echo(click.style(f"    - {err}", fg="red"))


def abort_on_schema_failure(result: SchemaCheckResult) -> None:
    """Raise a ClickException if schema validation failed."""
    if not result.valid:
        raise click.ClickException(
            f"Schema validation failed with {len(result.errors)} error(s). Aborting."
        )
