"""Embargo: prevent changes to specific paths during defined time windows."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class EmbargoViolation:
    path: str
    reason: str

    def __str__(self) -> str:
        return f"[embargo] {self.path}: {self.reason}"


@dataclass
class EmbargoResult:
    violations: List[EmbargoViolation] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)


@dataclass
class EmbargoWindow:
    label: str
    path_pattern: str
    start: str   # ISO-8601 datetime string
    end: str     # ISO-8601 datetime string

    def matches_path(self, path: str) -> bool:
        return bool(re.fullmatch(self.path_pattern.replace("*", ".*"), path))

    def is_active(self, now: Optional[datetime] = None) -> bool:
        if now is None:
            now = datetime.now(tz=timezone.utc)
        start_dt = datetime.fromisoformat(self.start)
        end_dt = datetime.fromisoformat(self.end)
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)
        return start_dt <= now < end_dt


@dataclass
class EmbargoConfig:
    windows: List[EmbargoWindow] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "EmbargoConfig":
        windows = [
            EmbargoWindow(
                label=w.get("label", ""),
                path_pattern=w["path_pattern"],
                start=w["start"],
                end=w["end"],
            )
            for w in data.get("windows", [])
        ]
        return cls(windows=windows)


def check_embargo(
    paths: List[str],
    config: EmbargoConfig,
    now: Optional[datetime] = None,
) -> EmbargoResult:
    result = EmbargoResult()
    for path in paths:
        for window in config.windows:
            if window.matches_path(path) and window.is_active(now):
                reason = f"embargoed by '{window.label}' until {window.end}"
                result.violations.append(EmbargoViolation(path=path, reason=reason))
                break
    return result
