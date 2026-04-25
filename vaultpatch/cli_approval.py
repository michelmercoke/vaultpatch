"""CLI commands for the approval gate feature."""
from __future__ import annotations

import click

from vaultpatch.approval_hook import (
    cmd_approve,
    cmd_list,
    cmd_revoke,
)

DEFAULT_FILE = "approvals.json"


@click.group("approval")
def approval_cmd() -> None:
    """Manage change approvals for Vault paths."""


@approval_cmd.command("approve")
@click.argument("path")
@click.option("--by", "approved_by", required=True, help="Approver identity.")
@click.option("--comment", default="", help="Optional approval comment.")
@click.option(
    "--file",
    "approval_file",
    default=DEFAULT_FILE,
    show_default=True,
    help="Path to approval store file.",
)
def approve_cmd(path: str, approved_by: str, comment: str, approval_file: str) -> None:
    """Record an approval for a Vault PATH."""
    cmd_approve(path, approved_by, comment, approval_file)


@approval_cmd.command("revoke")
@click.argument("path")
@click.option(
    "--file",
    "approval_file",
    default=DEFAULT_FILE,
    show_default=True,
    help="Path to approval store file.",
)
def revoke_cmd(path: str, approval_file: str) -> None:
    """Remove an existing approval for a Vault PATH."""
    cmd_revoke(path, approval_file)


@approval_cmd.command("list")
@click.option(
    "--file",
    "approval_file",
    default=DEFAULT_FILE,
    show_default=True,
    help="Path to approval store file.",
)
def list_cmd(approval_file: str) -> None:
    """List all recorded approvals."""
    cmd_list(approval_file)
