"""CLI hooks for rotation checking and recording."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

import click

from vaultpatch.rotation import RotationResult, RotationStore

_DEFAULT_STORE = Path(".vaultpatch_rotation.json")


def load_store(store_path: Optional[Path] = None) -> RotationStore:
    p = store_path or _DEFAULT_STORE
    if p.exists():
        return RotationStore.load(p)
    return RotationStore()


def save_store(store: RotationStore, store_path: Optional[Path] = None) -> None:
    p = store_path or _DEFAULT_STORE
    store.save(p)


def run_rotation_check(paths: List[str], store_path: Optional[Path] = None) -> RotationResult:
    store = load_store(store_path)
    return store.check(paths)


def echo_rotation_results(result: RotationResult) -> None:
    for warning in result.warnings:
        click.echo(f"[rotation] WARN  {warning}")
    for violation in result.violations:
        click.echo(f"[rotation] OVERDUE {violation}", err=True)
    if not result.warnings and not result.violations:
        click.echo("[rotation] All secrets rotated within policy.")


def record_rotation(path: str, max_age_days: int, store_path: Optional[Path] = None) -> None:
    store = load_store(store_path)
    entry = store.record(path, max_age_days)
    save_store(store, store_path)
    click.echo(f"[rotation] Recorded rotation for {path!r} at {entry.rotated_at}")


def abort_on_rotation_violation(result: RotationResult) -> None:
    if result.has_violations:
        click.echo(f"[rotation] {len(result.violations)} overdue secret(s). Aborting.", err=True)
        sys.exit(1)
