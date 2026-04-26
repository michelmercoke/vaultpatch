"""masking_hook.py — integrate MaskingConfig with diff/report display helpers."""
from __future__ import annotations

from typing import List

import click

from vaultpatch.diff import SecretDiff
from vaultpatch.masking import MaskingConfig, mask_value


def apply_masking_to_diffs(
    diffs: List[SecretDiff],
    config: MaskingConfig,
) -> List[SecretDiff]:
    """Return a new list of SecretDiff objects with values masked for display."""
    masked: List[SecretDiff] = []
    for d in diffs:
        old_masked = mask_value(d.key, d.old_value, config).masked
        new_masked = mask_value(d.key, d.new_value, config).masked
        masked.append(
            SecretDiff(
                path=d.path,
                key=d.key,
                old_value=old_masked,
                new_value=new_masked,
            )
        )
    return masked


def echo_masked_diffs(
    diffs: List[SecretDiff],
    config: MaskingConfig,
) -> None:
    """Print masked diff output to stdout using click."""
    display = apply_masking_to_diffs(diffs, config)
    for d in display:
        if d.old_value is None:
            click.echo(f"  + [{d.path}] {d.key} = {d.new_value}")
        elif d.new_value is None:
            click.echo(f"  - [{d.path}] {d.key} (removed)")
        else:
            click.echo(f"  ~ [{d.path}] {d.key}: {d.old_value} -> {d.new_value}")
