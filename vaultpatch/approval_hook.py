"""Approval hook — wire approval checks into the CLI apply flow."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import click

from vaultpatch.approval import (
    ApprovalResult,
    ApprovalStore,
    check_approvals,
    load_store,
    save_store,
)


def resolve_store(approval_file: str) -> ApprovalStore:
    return load_store(Path(approval_file))


def run_approval_check(
    paths: List[str], store: ApprovalStore
) -> ApprovalResult:
    return check_approvals(paths, store)


def echo_approval_results(result: ApprovalResult) -> None:
    if not result.has_violations:
        click.echo("[approval] All paths approved.")
        return
    for v in result.violations:
        click.echo(f"[approval] MISSING: {v}", err=True)


def abort_on_approval_failure(result: ApprovalResult) -> None:
    if result.has_violations:
        click.echo(
            f"[approval] {len(result.violations)} path(s) lack approval — aborting.",
            err=True,
        )
        sys.exit(1)


def cmd_approve(
    path: str,
    approved_by: str,
    comment: str,
    approval_file: str,
) -> None:
    store = load_store(Path(approval_file))
    entry = store.approve(path, approved_by, comment)
    save_store(store, Path(approval_file))
    click.echo(f"[approval] Approved '{entry.path}' by '{entry.approved_by}'.")


def cmd_revoke(path: str, approval_file: str) -> None:
    store = load_store(Path(approval_file))
    removed = store.revoke(path)
    if removed:
        save_store(store, Path(approval_file))
        click.echo(f"[approval] Revoked approval for '{path}'.")
    else:
        click.echo(f"[approval] No approval found for '{path}'.")


def cmd_list(approval_file: str) -> None:
    store = load_store(Path(approval_file))
    entries = store.all()
    if not entries:
        click.echo("[approval] No approvals recorded.")
        return
    for e in entries:
        click.echo(f"  {e.path}  approved_by={e.approved_by}  at={e.approved_at}  comment={e.comment!r}")
