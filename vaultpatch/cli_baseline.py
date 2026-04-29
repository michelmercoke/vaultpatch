"""CLI commands for managing secret baselines."""
from __future__ import annotations

import click
from pathlib import Path

from vaultpatch.baseline import load_baseline, save_baseline, BaselineStore
from vaultpatch.baseline_hook import capture_baseline, echo_baseline_summary, load_or_empty
from vaultpatch.config import VaultPatchConfig
from vaultpatch.fetch import fetch_secrets


@click.group("baseline")
def baseline_cmd() -> None:
    """Manage secret baselines for drift anchoring."""


@baseline_cmd.command("capture")
@click.option("--config", "config_path", default="vaultpatch.yaml", show_default=True)
@click.option("--namespace", required=True, help="Namespace to capture baseline for.")
@click.option("--output", default=".vaultpatch/baseline.json", show_default=True)
@click.option("--label", default=None, help="Optional label for this baseline snapshot.")
@click.option("--merge", is_flag=True, default=False, help="Merge into existing baseline file.")
def capture_cmd(config_path: str, namespace: str, output: str, label: str, merge: bool) -> None:
    """Capture current secrets as a baseline."""
    cfg = VaultPatchConfig.from_file(Path(config_path))
    ns_cfg = cfg.get_namespace(namespace)
    result = fetch_secrets(ns_cfg)
    incoming = capture_baseline({p: r for p, r in zip(ns_cfg.paths, result)}, namespace, label=label)

    out_path = Path(output)
    if merge:
        store = load_or_empty(out_path)
        from vaultpatch.baseline_hook import merge_into_store
        store = merge_into_store(store, incoming)
    else:
        store = incoming

    save_baseline(store, out_path)
    click.echo(f"Baseline saved to {out_path}")
    echo_baseline_summary(store)


@baseline_cmd.command("show")
@click.option("--file", "baseline_path", default=".vaultpatch/baseline.json", show_default=True)
@click.option("--namespace", default=None)
@click.option("--verbose", is_flag=True, default=False)
def show_cmd(baseline_path: str, namespace: str, verbose: bool) -> None:
    """Display contents of a saved baseline."""
    path = Path(baseline_path)
    store = load_baseline(path)
    entries = store.all()
    if namespace:
        entries = [e for e in entries if e.namespace == namespace]
    for e in sorted(entries, key=lambda x: (x.namespace, x.path)):
        label_str = f" [{e.label}]" if e.label else ""
        click.echo(f"{e.namespace}/{e.path}{label_str}")
        if verbose:
            for k, v in sorted(e.secrets.items()):
                click.echo(f"    {k}: {v}")


@baseline_cmd.command("clear")
@click.option("--file", "baseline_path", default=".vaultpatch/baseline.json", show_default=True)
@click.option("--namespace", required=True)
@click.option("--path", "secret_path", required=True)
def clear_cmd(baseline_path: str, namespace: str, secret_path: str) -> None:
    """Remove a single path entry from the baseline."""
    path = Path(baseline_path)
    store = load_baseline(path)
    removed = store.remove(namespace, secret_path)
    if removed:
        save_baseline(store, path)
        click.echo(f"Removed {namespace}/{secret_path} from baseline.")
    else:
        click.echo(f"Entry not found: {namespace}/{secret_path}", err=True)
