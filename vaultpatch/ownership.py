"""Ownership tracking for secret paths.

Allows teams or individuals to declare ownership of secret paths,
and flags diffs that touch paths without a registered owner.
"""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import List, Optional

from vaultpatch.diff import SecretDiff


@dataclass
class OwnershipRule:
    path_pattern: str
    owner: str
    team: Optional[str] = None

    def matches(self, path: str) -> bool:
        return fnmatch.fnmatch(path, self.path_pattern)


@dataclass
class OwnershipViolation:
    path: str
    message: str

    def __str__(self) -> str:
        return f"[ownership] {self.path}: {self.message}"


@dataclass
class OwnershipResult:
    violations: List[OwnershipViolation] = field(default_factory=list)
    assignments: List[tuple] = field(default_factory=list)  # (path, owner, team)

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)


@dataclass
class OwnershipConfig:
    rules: List[OwnershipRule] = field(default_factory=list)
    require_owner: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "OwnershipConfig":
        rules = [
            OwnershipRule(
                path_pattern=r["path"],
                owner=r["owner"],
                team=r.get("team"),
            )
            for r in data.get("rules", [])
        ]
        return cls(rules=rules, require_owner=data.get("require_owner", True))


def check_ownership(
    diffs: dict[str, List[SecretDiff]],
    config: OwnershipConfig,
) -> OwnershipResult:
    """Check that every changed path has a registered owner."""
    result = OwnershipResult()

    for path, path_diffs in diffs.items():
        if not path_diffs:
            continue

        matched_rule: Optional[OwnershipRule] = None
        for rule in config.rules:
            if rule.matches(path):
                matched_rule = rule
                break

        if matched_rule is not None:
            result.assignments.append((path, matched_rule.owner, matched_rule.team))
        elif config.require_owner:
            result.violations.append(
                OwnershipViolation(
                    path=path,
                    message="no owner registered for this path",
                )
            )

    return result
