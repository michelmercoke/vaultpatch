"""Apply a set of secret diffs to a Vault namespace."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from vaultpatch.diff import SecretDiff

logger = logging.getLogger(__name__)


@dataclass
class PatchResult:
    path: str
    applied: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return not self.errors


# Type alias for the write callable injected for testing / real Vault clients.
WriteFn = Callable[[str, dict[str, Any]], None]


def apply_diffs(
    diffs: list[SecretDiff],
    current_secrets: dict[str, Any],
    write_fn: WriteFn,
    dry_run: bool = False,
) -> list[PatchResult]:
    """Apply diffs grouped by path using *write_fn* to persist changes.

    Args:
        diffs: List of SecretDiff objects to apply.
        current_secrets: Full current secret data keyed by path, used to
            merge only changed keys before writing.
        write_fn: Callable(path, data) that writes a secret to Vault.
        dry_run: If True, log intended changes but do not call write_fn.

    Returns:
        A list of PatchResult, one per affected path.
    """
    # Group diffs by path
    by_path: dict[str, list[SecretDiff]] = {}
    for d in diffs:
        by_path.setdefault(d.path, []).append(d)

    results: list[PatchResult] = []
    for path, path_diffs in by_path.items():
        result = PatchResult(path=path)
        merged = dict(current_secrets.get(path, {}))

        for d in path_diffs:
            if d.is_removed:
                merged.pop(d.key, None)
            else:
                merged[d.key] = d.new_value
            result.applied.append(d.key)

        if dry_run:
            logger.info("[dry-run] Would write %s with keys: %s", path, list(merged))
        else:
            try:
                write_fn(path, merged)
                logger.info("Wrote %s (%d keys updated)", path, len(result.applied))
            except Exception as exc:  # noqa: BLE001
                for key in result.applied:
                    result.errors[key] = str(exc)
                result.applied.clear()

        results.append(result)
    return results
