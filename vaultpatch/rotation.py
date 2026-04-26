"""Secret rotation tracking: record when a secret was last rotated and flag overdue paths."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

_VERSION = 1
_DATE_FMT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass
class RotationViolation:
    path: str
    days_overdue: int

    def __str__(self) -> str:
        return f"{self.path}: overdue by {self.days_overdue} day(s)"


@dataclass
class RotationResult:
    violations: List[RotationViolation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)


@dataclass
class RotationEntry:
    path: str
    rotated_at: str  # ISO-8601
    max_age_days: int

    def is_overdue(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(timezone.utc)
        rotated = datetime.strptime(self.rotated_at, _DATE_FMT).replace(tzinfo=timezone.utc)
        return (now - rotated) > timedelta(days=self.max_age_days)

    def days_overdue(self, now: Optional[datetime] = None) -> int:
        now = now or datetime.now(timezone.utc)
        rotated = datetime.strptime(self.rotated_at, _DATE_FMT).replace(tzinfo=timezone.utc)
        overdue = (now - rotated) - timedelta(days=self.max_age_days)
        return max(0, overdue.days)

    def to_dict(self) -> dict:
        return {"path": self.path, "rotated_at": self.rotated_at, "max_age_days": self.max_age_days}


class RotationStore:
    def __init__(self, entries: Optional[Dict[str, RotationEntry]] = None):
        self._entries: Dict[str, RotationEntry] = entries or {}

    def record(self, path: str, max_age_days: int, now: Optional[datetime] = None) -> RotationEntry:
        ts = (now or datetime.now(timezone.utc)).strftime(_DATE_FMT)
        entry = RotationEntry(path=path, rotated_at=ts, max_age_days=max_age_days)
        self._entries[path] = entry
        return entry

    def get(self, path: str) -> Optional[RotationEntry]:
        return self._entries.get(path)

    def check(self, paths: List[str], now: Optional[datetime] = None) -> RotationResult:
        result = RotationResult()
        for path in paths:
            entry = self._entries.get(path)
            if entry is None:
                result.warnings.append(f"{path}: no rotation record found")
            elif entry.is_overdue(now):
                result.violations.append(RotationViolation(path=path, days_overdue=entry.days_overdue(now)))
        return result

    def save(self, path: Path) -> None:
        data = {"version": _VERSION, "entries": {k: v.to_dict() for k, v in self._entries.items()}}
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path) -> "RotationStore":
        data = json.loads(path.read_text())
        if data.get("version") != _VERSION:
            raise ValueError(f"Unsupported rotation store version: {data.get('version')}")
        entries = {
            k: RotationEntry(**v) for k, v in data.get("entries", {}).items()
        }
        return cls(entries=entries)
