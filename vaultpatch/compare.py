"""Compare fetched secrets across two namespaces and produce diffs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from vaultpatch.diff import SecretDiff, compute_diffs
from vaultpatch.fetch import FetchResult


@dataclass
class CompareResult:
    source_namespace: str
    target_namespace: str
    diffs_by_path: Dict[str, List[SecretDiff]] = field(default_factory=dict)
    skipped_paths: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(self.diffs_by_path.values())

    def total_changes(self) -> int:
        return sum(len(d) for d in self.diffs_by_path.values())


def compare_results(
    source: FetchResult,
    target: FetchResult,
    paths: list[str],
) -> CompareResult:
    """Compare source and target FetchResults path-by-path."""
    result = CompareResult(
        source_namespace=source.namespace,
        target_namespace=target.namespace,
    )

    for path in paths:
        if path in source.errors or path in target.errors:
            result.skipped_paths.append(path)
            continue

        src_secrets = source.secrets.get(path, {})
        tgt_secrets = target.secrets.get(path, {})
        diffs = compute_diffs(src_secrets, tgt_secrets)
        result.diffs_by_path[path] = diffs

    return result
