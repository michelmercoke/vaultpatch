"""Hook: run anomaly checks and integrate with CLI flow."""
from __future__ import annotations

import sys
from typing import Dict, List, Optional

import click

from vaultpatch.anomaly import AnomalyConfig, AnomalyResult, check_anomalies
from vaultpatch.diff import SecretDiff


def run_anomaly_check(
    diffs_by_path: Dict[str, List[SecretDiff]],
    cfg: Optional[AnomalyConfig] = None,
) -> Dict[str, AnomalyResult]:
    """Run anomaly detection for every path in *diffs_by_path*."""
    return {
        path: check_anomalies(path, diffs, cfg)
        for path, diffs in diffs_by_path.items()
    }


def echo_anomaly_results(results: Dict[str, AnomalyResult]) -> None:
    """Print a human-readable summary to stdout / stderr."""
    any_violation = False
    for path, result in results.items():
        if not result.has_violations:
            click.echo(f"[anomaly] {path}: OK")
        else:
            any_violation = True
            for v in result.violations:
                click.echo(f"[anomaly] WARN  {v}", err=True)
    if not any_violation:
        click.echo("[anomaly] All paths passed anomaly checks.")


def abort_on_anomaly_failure(results: Dict[str, AnomalyResult]) -> None:
    """Exit with code 1 if any anomaly violations were found."""
    total = sum(len(r.violations) for r in results.values())
    if total:
        click.echo(
            f"[anomaly] {total} violation(s) detected — aborting.",
            err=True,
        )
        sys.exit(1)
