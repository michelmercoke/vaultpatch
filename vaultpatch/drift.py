"""Drift detection: compare live Vault secrets against a saved snapshot."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from vaultpatch.diff import SecretDiff, compute_diffs
from vaultpatch.fetch import FetchResult
from vaultpatch.snapshot import load_snapshot, snapshot_key


@dataclass
class DriftResult:
    namespace: str
    path: str
    diffs: List[SecretDiff] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def has_drift(self) -> bool:
        return bool(self.diffs)

    @property
    def success(self) -> bool:
        return self.error is None


def detect_drift(
    fetch_result: FetchResult,
    snapshot_dir: str,
    namespace: str,
) -> List[DriftResult]:
    """Compare each fetched path against the corresponding snapshot entry.

    Returns one DriftResult per path in the fetch result.
    """
    results: List[DriftResult] = []

    if not fetch_result.success:
        results.append(
            DriftResult(
                namespace=namespace,
                path="<fetch>",
                error=fetch_result.error,
            )
        )
        return results

    try:
        key = snapshot_key(namespace)
        snapshot: Dict[str, Dict[str, str]] = load_snapshot(snapshot_dir, key)
    except (FileNotFoundError, ValueError) as exc:
        results.append(
            DriftResult(
                namespace=namespace,
                path="<snapshot>",
                error=str(exc),
            )
        )
        return results

    for path, live_secrets in fetch_result.secrets.items():
        baseline = snapshot.get(path, {})
        diffs = compute_diffs(baseline, live_secrets)
        results.append(DriftResult(namespace=namespace, path=path, diffs=diffs))

    return results


def summarise_drift(results: List[DriftResult]) -> str:
    """Return a human-readable one-line summary of drift results."""
    errors = [r for r in results if not r.success]
    drifted = [r for r in results if r.success and r.has_drift]
    clean = [r for r in results if r.success and not r.has_drift]
    return (
        f"{len(drifted)} path(s) drifted, "
        f"{len(clean)} clean, "
        f"{len(errors)} error(s)"
    )
