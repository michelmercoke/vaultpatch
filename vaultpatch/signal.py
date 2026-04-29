"""Signal detection: identify secrets whose values match known-bad patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from vaultpatch.diff import SecretDiff

# Patterns that indicate a secret may be a default, placeholder, or leaked value.
_DEFAULT_PATTERNS: List[str] = [
    r"^changeme$",
    r"^password$",
    r"^secret$",
    r"^todo$",
    r"^fixme$",
    r"^replace[_-]?me$",
    r"^<.*>$",        # XML/template placeholder like <MY_SECRET>
    r"^\$\{.*\}$",   # Shell/template placeholder like ${MY_VAR}
    r"^0+$",          # All zeros
]


@dataclass
class SignalViolation:
    path: str
    key: str
    pattern: str
    value_snippet: str

    def __str__(self) -> str:
        return (
            f"{self.path}:{self.key} matches signal pattern '{self.pattern}' "
            f"(value: '{self.value_snippet}')"
        )


@dataclass
class SignalConfig:
    extra_patterns: List[str] = field(default_factory=list)
    ignore_keys: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "SignalConfig":
        return cls(
            extra_patterns=data.get("extra_patterns", []),
            ignore_keys=data.get("ignore_keys", []),
        )

    @property
    def compiled(self) -> List[re.Pattern]:
        all_patterns = _DEFAULT_PATTERNS + self.extra_patterns
        return [re.compile(p, re.IGNORECASE) for p in all_patterns]


@dataclass
class SignalResult:
    violations: List[SignalViolation] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)


def check_signals(
    path: str,
    diffs: List[SecretDiff],
    config: Optional[SignalConfig] = None,
) -> SignalResult:
    """Check diffs for values matching known-bad signal patterns."""
    cfg = config or SignalConfig()
    compiled = cfg.compiled
    violations: List[SignalViolation] = []

    for diff in diffs:
        if diff.is_removed():
            continue
        if diff.key in cfg.ignore_keys:
            continue
        value = diff.new_value or ""
        snippet = value[:40]
        for pattern in compiled:
            if pattern.search(value):
                violations.append(
                    SignalViolation(
                        path=path,
                        key=diff.key,
                        pattern=pattern.pattern,
                        value_snippet=snippet,
                    )
                )
                break  # one violation per key

    return SignalResult(violations=violations)
