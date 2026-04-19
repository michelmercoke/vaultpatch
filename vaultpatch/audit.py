"""Audit log writer for vaultpatch operations."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from vaultpatch.diff import SecretDiff


@dataclass
class AuditEntry:
    timestamp: str
    namespace: str
    path: str
    operation: str  # "diff" | "apply"
    changes: List[dict] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_entry(
    namespace: str,
    path: str,
    operation: str,
    diffs: List[SecretDiff],
    error: Optional[str] = None,
) -> AuditEntry:
    changes = [
        {"key": d.key, "label": d.label()}
        for d in diffs
        if d.is_changed() or d.is_added() or d.is_removed()
    ]
    return AuditEntry(
        timestamp=_now_iso(),
        namespace=namespace,
        path=path,
        operation=operation,
        changes=changes,
        error=error,
    )


def write_audit_log(entries: List[AuditEntry], log_path: str) -> None:
    """Append audit entries as newline-delimited JSON."""
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry.to_dict()) + "\n")


def load_audit_log(log_path: str) -> List[AuditEntry]:
    """Read all audit entries from a newline-delimited JSON file."""
    path = Path(log_path)
    if not path.exists():
        return []
    entries: List[AuditEntry] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                data = json.loads(line)
                entries.append(AuditEntry(**data))
    return entries
