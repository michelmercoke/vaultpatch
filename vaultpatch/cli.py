"""CLI entry point for vaultpatch."""

import sys
import click

from vaultpatch.config import VaultPatchConfig
from vaultpatch.fetch import fetch_secrets
from vaultpatch.compare import compare_results
from vaultpatch.report import Report
from vaultpatch.patch import apply_diffs


@click.group()
def cli():
    """vaultpatch — diff and apply secret changes across Vault namespaces."""


@cli.command()
@click.option("--config", "-c", required=True, help="Path to vaultpatch YAML config.")
@click.option("--namespace", "-n", multiple=True, help="Limit to specific namespaces.")
def diff(config, namespace):
    """Show a diff of secrets across namespaces."""
    cfg = VaultPatchConfig.from_file(config)
    report = Report()

    namespaces = namespace or [ns.name for ns in cfg.namespaces]

    for ns_name in namespaces:
        ns_cfg = cfg.get_namespace(ns_name)
        if ns_cfg is None:
            click.echo(f"[warn] namespace '{ns_name}' not found in config", err=True)
            continue

        result = fetch_secrets(ns_cfg)
        if not result.success:
            click.echo(f"[error] {ns_name}: {result.error}", err=True)
            continue

        compare = compare_results([result])
        report.add(ns_name, compare.diffs)

    if report.total_changes() == 0:
        click.echo("No changes detected.")
        return

    for entry in report.entries:
        click.echo(f"\n=== {entry.namespace} ===")
        for d in entry.diffs:
            click.echo(f"  {d.label()}  {d.key}")

    click.echo(f"\nTotal changes: {report.total_changes()}")


@cli.command()
@click.option("--config", "-c", required=True, help="Path to vaultpatch YAML config.")
@click.option("--namespace", "-n", multiple=True, help="Limit to specific namespaces.")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without applying.")
def apply(config, namespace, dry_run):
    """Apply secret diffs to Vault namespaces."""
    cfg = VaultPatchConfig.from_file(config)
    namespaces = namespace or [ns.name for ns in cfg.namespaces]

    for ns_name in namespaces:
        ns_cfg = cfg.get_namespace(ns_name)
        if ns_cfg is None:
            click.echo(f"[warn] namespace '{ns_name}' not found in config", err=True)
            continue

        result = fetch_secrets(ns_cfg)
        if not result.success:
            click.echo(f"[error] {ns_name}: {result.error}", err=True)
            continue

        compare = compare_results([result])
        if not compare.has_changes():
            click.echo(f"[{ns_name}] No changes.")
            continue

        if dry_run:
            click.echo(f"[{ns_name}] Dry run — {compare.total_changes()} change(s) skipped.")
            continue

        patch_result = apply_diffs(ns_cfg, compare.diffs)
        status = "OK" if patch_result.success else f"FAILED: {patch_result.error}"
        click.echo(f"[{ns_name}] {status}")


if __name__ == "__main__":
    cli()
