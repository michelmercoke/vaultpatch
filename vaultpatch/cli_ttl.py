"""CLI sub-command: vaultpatch ttl — check secret expiry across namespaces."""
from __future__ import annotations

import sys
from datetime import datetime, timezone, timedelta

import click

from vaultpatch.config import VaultPatchConfig
from vaultpatch.ttl import check_ttl, TTLReport


def _echo_report(report: TTLReport, namespace: str) -> None:
    if report.expired:
        click.echo(click.style(f"[{namespace}] EXPIRED ({len(report.expired)} path(s)):", fg="red", bold=True))
        for e in report.expired:
            click.echo(f"  ✗ {e.path}  (expired {abs(round(e.days_remaining, 1))}d ago)")

    if report.warning:
        click.echo(click.style(f"[{namespace}] WARNING ({len(report.warning)} path(s) expiring soon):", fg="yellow"))
        for e in report.warning:
            click.echo(f"  ⚠ {e.path}  ({round(e.days_remaining, 1)}d remaining)")

    if report.healthy:
        click.echo(click.style(f"[{namespace}] OK ({len(report.healthy)} path(s) healthy)", fg="green"))


@click.group("ttl")
def ttl_cmd() -> None:
    """Commands for inspecting secret TTL / expiry metadata."""


@ttl_cmd.command("check")
@click.option("--config", "config_path", default="vaultpatch.yaml", show_default=True)
@click.option("--namespace", "ns_name", default=None, help="Limit check to a single namespace.")
@click.option("--warn-days", default=7, show_default=True, help="Days threshold for warnings.")
@click.option("--fail-on-expired", is_flag=True, default=False)
@click.pass_context
def check_cmd(ctx: click.Context, config_path: str, ns_name: str | None, warn_days: int, fail_on_expired: bool) -> None:
    """Check TTL metadata stored under each namespace's ttl_metadata config key."""
    cfg: VaultPatchConfig = VaultPatchConfig.from_file(config_path)
    namespaces = [cfg.get_namespace(ns_name)] if ns_name else list(cfg.namespaces.values())

    any_expired = False
    for ns in namespaces:
        raw: dict = getattr(ns, "ttl_metadata", {}) or {}
        report = check_ttl(raw, namespace=ns.name, warn_days=warn_days)
        _echo_report(report, ns.name)
        if report.expired:
            any_expired = True

    if fail_on_expired and any_expired:
        click.echo(click.style("Aborting: expired secrets detected.", fg="red"), err=True)
        sys.exit(1)
