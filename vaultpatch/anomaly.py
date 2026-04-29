"""Anomaly detection: flag secrets whose values deviate from expected patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from vaultpatch.diff import SecretDiff


@dataclass
class AnomalyViolation:
    path: str
    key: str
    reason: str

    def __str__(self) -> str:
        return f"{self.path}:{self.key} — {self.reason}"


@dataclass
class AnomalyResult:
    violations: List[AnomalyViolation] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)


@dataclass
class AnomalyConfig:
    min_length: int = 8
    max_length: int = 4096
    disallow_patterns: List[str] = field(default_factory=lambda: [
        r"^(password|secret|changeme|1234|admin)$",
    ])
    require_non_ascii_free: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "AnomalyConfig":
        return cls(
            min_length=data.get("min_length", 8),
            max_length=data.get("max_length", 4096),
            disallow_patterns=data.get("disallow_patterns", [
                r"^(password|secret|changeme|1234|admin)$",
            ]),
            require_non_ascii_free=data.get("require_non_ascii_free", True),
        )

    def compiled(self) -> List[re.Pattern]:
        return [re.compile(p, re.IGNORECASE) for p in self.disallow_patterns]


def check_anomalies(
    path: str,
    diffs: List[SecretDiff],
    cfg: Optional[AnomalyConfig] = None,
) -> AnomalyResult:
    if cfg is None:
        cfg = AnomalyConfig()
    patterns = cfg.compiled()
    violations: List[AnomalyViolation] = []

    for d in diffs:
        if d.is_removed:
            continue
        value = d.new_value or ""

        if len(value) < cfg.min_length:
            violations.append(AnomalyViolation(path, d.key,
                f"value too short ({len(value)} < {cfg.min_length})"))
            continue

        if len(value) > cfg.max_length:
            violations.append(AnomalyViolation(path, d.key,
                f"value too long ({len(value)} > {cfg.max_length})"))
            continue

        for pat in patterns:
            if pat.search(value):
                violations.append(AnomalyViolation(path, d.key,
                    f"value matches disallowed pattern '{pat.pattern}'"))
                break

        if cfg.require_non_ascii_free and not value.isascii():
            violations.append(AnomalyViolation(path, d.key,
                "value contains non-ASCII characters"))

    return AnomalyResult(violations=violations)
