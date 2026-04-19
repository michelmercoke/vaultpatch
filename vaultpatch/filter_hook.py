"""Integration helpers to apply FilterOptions inside CLI compare flow."""
from __future__ import annotations

from typing import Dict, List, Optional

from vaultpatch.compare import CompareResult
from vaultpatch.diff import SecretDiff
from vaultpatch.filter import FilterOptions, filter_diffs


def apply_filter_to_compare(
    result: CompareResult,
    path_prefix: Optional[str] = None,
    key_pattern: Optional[str] = None,
    change_types: Optional[List[str]] = None,
) -> CompareResult:
    """Return a new CompareResult with diffs filtered per namespace."""
    opts = FilterOptions(
        path_prefix=path_prefix,
        key_pattern=key_pattern,
        change_types=change_types or ["added", "removed", "changed"],
    )

    filtered: Dict[str, List[SecretDiff]] = {}
    for namespace, diffs in result.diffs_by_namespace.items():
        filtered[namespace] = filter_diffs(diffs, opts)

    return CompareResult(diffs_by_namespace=filtered, errors=result.errors)


def summarise_filter(opts: FilterOptions) -> str:
    parts = []
    if opts.path_prefix:
        parts.append(f"prefix={opts.path_prefix!r}")
    if opts.key_pattern:
        parts.append(f"key={opts.key_pattern!r}")
    if opts.change_types != ["added", "removed", "changed"]:
        parts.append(f"types={','.join(opts.change_types)}")
    return "Filter(" + ", ".join(parts) + ")" if parts else "Filter(none)"
