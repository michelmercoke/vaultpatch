"""Approval gate — require explicit sign-off before applying changes."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class ApprovalEntry:
    path: str
    approved_by: str
    approved_at: str
    comment: str = ""

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "comment": self.comment,
        }


@dataclass
class ApprovalStore:
    _entries: List[ApprovalEntry] = field(default_factory=list)

    def approve(self, path: str, approved_by: str, comment: str = "") -> ApprovalEntry:
        entry = ApprovalEntry(
            path=path,
            approved_by=approved_by,
            approved_at=datetime.now(timezone.utc).isoformat(),
            comment=comment,
        )
        self._entries = [e for e in self._entries if e.path != path]
        self._entries.append(entry)
        return entry

    def revoke(self, path: str) -> bool:
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.path != path]
        return len(self._entries) < before

    def get(self, path: str) -> Optional[ApprovalEntry]:
        return next((e for e in self._entries if e.path == path), None)

    def all(self) -> List[ApprovalEntry]:
        return list(self._entries)

    def to_dict(self) -> dict:
        return {"approvals": [e.to_dict() for e in self._entries]}


@dataclass
class ApprovalViolation:
    path: str

    def __str__(self) -> str:
        return f"Path '{self.path}' has no approval"


@dataclass
class ApprovalResult:
    violations: List[ApprovalViolation] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)


def check_approvals(paths: List[str], store: ApprovalStore) -> ApprovalResult:
    """Return violations for any path that lacks an approval entry."""
    violations = [
        ApprovalViolation(path=p) for p in paths if store.get(p) is None
    ]
    return ApprovalResult(violations=violations)


def save_store(store: ApprovalStore, filepath: Path) -> None:
    filepath.write_text(json.dumps(store.to_dict(), indent=2))


def load_store(filepath: Path) -> ApprovalStore:
    if not filepath.exists():
        return ApprovalStore()
    data = json.loads(filepath.read_text())
    entries = [
        ApprovalEntry(
            path=e["path"],
            approved_by=e["approved_by"],
            approved_at=e["approved_at"],
            comment=e.get("comment", ""),
        )
        for e in data.get("approvals", [])
    ]
    return ApprovalStore(_entries=entries)
