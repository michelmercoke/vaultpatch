"""CLI subcommand: vaultpatch scope check"""
from __future__ import annotations

import click

from vaultpatch.config import VaultPatchConfig
from vaultpatch.scope import ScopeConfig
from vaultpatch.scope_hook import abort_on_scope_violation, echo_scope_results, run_scope_check


@click.group("scope")
def scope_cmd() -> None:
    """Scope enforcement commands."""


@scope_cmd.command("check")
@click.option("--config", "config_path", default="vaultpatch.yaml", show_default=True)
@click.option("--namespace", required=True, help="Namespace to check.")
@click.option("--path", "paths", multiple=True, required=True, help="Path(s) to validate.")
@click.option(
    "--allowed-namespace",
    "allowed_namespaces",
    multiple=True,
    help="Allowed namespace glob patterns (overrides config).",
)
@click.option(
    "--allowed-path",
    "allowed_paths",
    multiple=True,
    help="Allowed path glob patterns (overrides config).",
)
@click.option("--dry-run", is_flag=True, default=False, help="Report but do not abort.")
def check_cmd(
    config_path: str,
    namespace: str,
    paths: tuple,
    allowed_namespaces: tuple,
    allowed_paths: tuple,
    dry_run: bool,
) -> None:
    """Check that namespace/paths fall within the permitted scope."""
    scope_cfg = ScopeConfig(
        allowed_namespaces=list(allowed_namespaces),
        allowed_paths=list(allowed_paths),
    )
    result = run_scope_check(scope_cfg, namespace, list(paths))
    echo_scope_results(result)
    if not dry_run:
        abort_on_scope_violation(result)
    elif result.has_violations:
        click.echo(
            f"dry-run: {len(result.violations)} scope violation(s) would abort.",
            err=True,
        )
