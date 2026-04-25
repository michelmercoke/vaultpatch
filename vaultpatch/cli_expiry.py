"""CLI sub-command for expiry checks."""
from __future__ import annotations

import click

from vaultpatch.config import VaultPatchConfig
from vaultpatch.fetch import fetch_secrets
from vaultpatch.expiry_hook import abort_on_expiry, echo_expiry_results, run_expiry_check


@click.group("expiry")
def expiry_cmd() -> None:
    """Commands for secret expiry management."""


@expiry_cmd.command("check")
@click.option("--config", "config_path", default="vaultpatch.yaml", show_default=True)
@click.option("--warn-days", default=14, show_default=True, help="Days ahead to warn before expiry.")
@click.option("--no-fail", is_flag=True, default=False, help="Exit 0 even when violations exist.")
def check_cmd(config_path: str, warn_days: int, no_fail: bool) -> None:
    """Check all configured namespaces for expired or soon-to-expire secrets."""
    cfg = VaultPatchConfig.from_file(config_path)

    path_secrets: dict = {}
    for ns in cfg.namespaces:
        result = fetch_secrets(ns)
        if result.success:
            for path, data in result.secrets.items():
                path_secrets[f"{ns.name}/{path}"] = data
        else:
            click.echo(f"[WARN] Could not fetch secrets for namespace '{ns.name}': {result.error}", err=True)

    results = run_expiry_check(path_secrets, warn_days=warn_days)
    echo_expiry_results(results)

    if not no_fail:
        abort_on_expiry(results)
