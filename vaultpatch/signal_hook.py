"""Hook wiring for signal detection into the CLI pipeline."""
from __future__ import annotations

import sys
from typing import Dict, List, Optional

import click

from vaultpatch.diff import SecretDiff
from vaultpatch.signal import SignalConfig, SignalResult, SignalViolation, check_signals


def run_signal_check(
    diffs_by_path: Dict[str, List[SecretDiff]],
    config: Optional[SignalConfig] = None,
) -> Dict[str, SignalResult]:
    """Run signal checks across all paths and return per-path results."""
    results: Dict[str, SignalResult] = {}
    for path, diffs in diffs_by_path.items():
        results[path] = check_signals(path, diffs, config)
    return results


def echo_signal_results(results: Dict[str, SignalResult]) -> None:
    """Print signal violations to stderr; print OK summary if none found."""
    total = sum(len(r.violations) for r in results.values())
    if total == 0:
        click.echo("[signal] No known-bad value patterns detected.")
        return

    click.echo(
        f"[signal] {total} signal violation(s) detected:", file=sys.stderr
    )
    for result in results.values():
        for v in result.violations:
            click.echo(f"  SIGNAL  {v}", file=sys.stderr)


def abort_on_signal_failure(results: Dict[str, SignalResult]) -> None:
    """Raise SystemExit if any signal violations exist."""
    total = sum(len(r.violations) for r in results.values())
    if total:
        raise SystemExit(
            f"[signal] Aborting: {total} known-bad value pattern(s) found."
        )
