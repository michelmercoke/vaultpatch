"""Hook that applies template rendering inside the CLI diff/apply pipeline."""

from __future__ import annotations

from typing import Dict, Optional

import click

from vaultpatch.template import TemplateResult, render_secrets


def apply_templates(
    secrets: Dict[str, str],
    env: Optional[Dict[str, str]] = None,
) -> TemplateResult:
    """Render *secrets* and return the result (caller decides how to handle errors)."""
    return render_secrets(secrets, env=env)


def echo_template_errors(result: TemplateResult) -> None:
    """Print any template errors to stderr via Click."""
    for err in result.errors:
        click.echo(click.style(f"  template error: {err}", fg="red"), err=True)


def abort_on_template_failure(result: TemplateResult) -> None:
    """Abort the CLI process if *result* contains errors."""
    if not result.success:
        echo_template_errors(result)
        raise click.Abort()
