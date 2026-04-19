"""Thin integration layer: collect audit entries during CLI runs."""
from __future__ import annotations

import os
from typing import List, Optional

from vaultpatch.audit import AuditEntry, build_entry, write_audit_log
from vaultpatch.compare import CompareResult
from vaultpatch.diff import SecretDiff

DEFAULT_LOG_PATH = os.environ.get("VAULTPATCH_AUDIT_LOG", "vaultpatch-audit.log")


def entries_from_compare(
    namespace: str,
    operation: str,
    result: CompareResult,
) -> List[AuditEntry]:
    """Convert a CompareResult into a list of AuditEntry objects."""
    entries: List[AuditEntry] = []
    for path, diffs in result.diffs_by_path.items():
        entries.append(
            build_entry(
                namespace=namespace,
                path=path,
                operation=operation,
                diffs=diffs,
            )
        )
    for path, err in result.errors.items():
        entries.append(
            build_entry(
                namespace=namespace,
                path=path,
                operation=operation,
                diffs=[],
                error=err,
            )
        )
    return entries


def record(
    namespace: str,
    operation: str,
    result: CompareResult,
    log_path: Optional[str] = None,
) -> None:
    """Build audit entries from *result* and append them to the audit log."""
    entries = entries_from_compare(namespace, operation, result)
    if entries:
        write_audit_log(entries, log_path or DEFAULT_LOG_PATH)
