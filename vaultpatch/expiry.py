"""Secret expiry tracking — flag secrets that are approaching or past their expiry date."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

_DATE_FMT = "%Y-%m-%d"
_EXPIRY_KEY = "__expires_at"


@dataclass
class ExpiryViolation:
    path: str
    key: str
    expires_at: str
    days_overdue: int

    def __str__(self) -> str:
        return f"{self.path}/{self.key} expired {self.days_overdue}d ago ({self.expires_at})"


@dataclass
class ExpiryWarning:
    path: str
    key: str
    expires_at: str
    days_remaining: int

    def __str__(self) -> str:
        return f"{self.path}/{self.key} expires in {self.days_remaining}d ({self.expires_at})"


@dataclass
class ExpiryResult:
    violations: List[ExpiryViolation] = field(default_factory=list)
    warnings: List[ExpiryWarning] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)


def _today() -> datetime:
    return datetime.now(tz=timezone.utc)


def check_expiry(
    path: str,
    secrets: Dict[str, str],
    warn_days: int = 14,
) -> ExpiryResult:
    """Inspect *secrets* for expiry metadata and return violations/warnings."""
    result = ExpiryResult()
    today = _today()

    for key, value in secrets.items():
        if not key.endswith(_EXPIRY_KEY) and key != _EXPIRY_KEY:
            continue
        try:
            expiry_dt = datetime.strptime(value, _DATE_FMT).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

        delta = (expiry_dt - today).days
        if delta < 0:
            result.violations.append(
                ExpiryViolation(path=path, key=key, expires_at=value, days_overdue=abs(delta))
            )
        elif delta <= warn_days:
            result.warnings.append(
                ExpiryWarning(path=path, key=key, expires_at=value, days_remaining=delta)
            )

    return result


def summarise_expiry(results: List[ExpiryResult]) -> str:
    total_v = sum(len(r.violations) for r in results)
    total_w = sum(len(r.warnings) for r in results)
    return f"Expiry check: {total_v} violation(s), {total_w} warning(s)"
