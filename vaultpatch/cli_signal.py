"""CLI subcommand for signal detection."""
from __future__ import annotations

from typing import Optional

import click

from vaultpatch.config import VaultPatchConfig
from vaultpatch.fetch import fetch_secrets
from vaultpatch.diff import SecretDiff
from vaultpatch.signal import SignalConfig
from vaultpatch.signal_hook import echo_signal_results, run_signal_check, abort_on_signal_failure


@click.group("signal")
def signal_cmd() -> None:
    """Detect known-bad or placeholder secret values."""


@signal_cmd.command("check")
@click.option("--config", "config_path", default="vaultpatch.yaml", show_default=True)
@click.option("--namespace", default=None, help="Limit check to one namespace.")
@click.option("--fail/--no-fail", default=True, show_default=True,
              help="Exit non-zero when violations are found.")
def check_cmd(config_path: str, namespace: Optional[str], fail: bool) -> None:
    """Scan live secrets for known-bad value patterns."""
    cfg = VaultPatchConfig.from_file(config_path)
    namespaces = (
        [cfg.get_namespace(namespace)] if namespace else cfg.namespaces
    )

    signal_cfg = SignalConfig()
    all_diffs: dict = {}

    for ns in namespaces:
        result = fetch_secrets(ns)
        for path, secrets in result.secrets.items():
            # Treat every live value as a potential "new" value for signal scanning.
            diffs = [
                SecretDiff(key=k, old_value=None, new_value=v)
                for k, v in secrets.items()
            ]
            all_diffs[f"{ns.namespace}/{path}"] = diffs

    results = run_signal_check(all_diffs, signal_cfg)
    echo_signal_results(results)
    if fail:
        abort_on_signal_failure(results)
