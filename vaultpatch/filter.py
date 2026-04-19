"""Filter diffs by path prefix or key pattern."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import List, Optional

from vaultpatch.diff import SecretDiff


@dataclass
class FilterOptions:
    path_prefix: Optional[str] = None
    key_pattern: Optional[str] = None
    change_types: List[str] = field(default_factory=lambda: ["added", "removed", "changed"])


def _matches_change_type(diff: SecretDiff, change_types: List[str]) -> bool:
    if diff.is_added() and "added" in change_types:
        return True
    if diff.is_removed() and "removed" in change_types:
        return True
    if diff.is_changed() and "changed" in change_types:
        return True
    return False


def filter_diffs(diffs: List[SecretDiff], options: FilterOptions) -> List[SecretDiff]:
    """Return diffs matching all active filter criteria."""
    result = []
    for diff in diffs:
        if options.path_prefix and not diff.path.startswith(options.path_prefix):
            continue
        if options.key_pattern and not fnmatch.fnmatch(diff.key, options.key_pattern):
            continue
        if not _matches_change_type(diff, options.change_types):
            continue
        result.append(diff)
    return result


def filter_by_prefix(diffs: List[SecretDiff], prefix: str) -> List[SecretDiff]:
    return [d for d in diffs if d.path.startswith(prefix)]


def filter_by_key(diffs: List[SecretDiff], pattern: str) -> List[SecretDiff]:
    return [d for d in diffs if fnmatch.fnmatch(d.key, pattern)]
