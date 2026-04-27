"""Cascade: propagate secret changes from a source path to dependent paths."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CascadeRule:
    source: str
    targets: List[str]
    keys: Optional[List[str]] = None  # None means all keys

    def matches_source(self, path: str) -> bool:
        return self.source == path

    def applies_to_key(self, key: str) -> bool:
        return self.keys is None or key in self.keys


@dataclass
class CascadeViolation:
    source: str
    target: str
    key: str
    reason: str

    def __str__(self) -> str:
        return f"cascade {self.source} -> {self.target} [{self.key}]: {self.reason}"


@dataclass
class CascadeResult:
    propagations: Dict[str, Dict[str, str]] = field(default_factory=dict)  # target -> {key: value}
    violations: List[CascadeViolation] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)

    @property
    def total_propagations(self) -> int:
        return sum(len(kv) for kv in self.propagations.values())


def build_cascade(
    source_path: str,
    source_secrets: Dict[str, str],
    rules: List[CascadeRule],
) -> CascadeResult:
    """Determine which target paths and keys should receive propagated values."""
    result = CascadeResult()
    for rule in rules:
        if not rule.matches_source(source_path):
            continue
        for target in rule.targets:
            for key, value in source_secrets.items():
                if not rule.applies_to_key(key):
                    continue
                if not value:
                    result.violations.append(
                        CascadeViolation(
                            source=source_path,
                            target=target,
                            key=key,
                            reason="blank value cannot be cascaded",
                        )
                    )
                    continue
                result.propagations.setdefault(target, {})[key] = value
    return result


def rules_from_dict(raw: List[Dict]) -> List[CascadeRule]:
    """Parse a list of raw dicts (e.g. from YAML config) into CascadeRule objects."""
    rules = []
    for item in raw:
        rules.append(
            CascadeRule(
                source=item["source"],
                targets=item["targets"],
                keys=item.get("keys"),
            )
        )
    return rules
