"""Access control: restrict which namespaces/paths a token may touch."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import List, Optional


@dataclass
class AccessRule:
    namespace: str          # glob pattern, e.g. "prod/*" or "*"
    path: str               # glob pattern, e.g. "secret/app/*"
    allow: bool = True

    def matches(self, namespace: str, path: str) -> bool:
        return fnmatch(namespace, self.namespace) and fnmatch(path, self.path)


@dataclass
class AccessViolation:
    namespace: str
    path: str
    reason: str

    def __str__(self) -> str:
        return f"[{self.namespace}] {self.path}: {self.reason}"


@dataclass
class AccessResult:
    violations: List[AccessViolation] = field(default_factory=list)

    @property
    def allowed(self) -> bool:
        return len(self.violations) == 0


def check_access(
    namespace: str,
    paths: List[str],
    rules: List[AccessRule],
    default_allow: bool = True,
) -> AccessResult:
    """Evaluate *rules* for every (namespace, path) pair.

    Rules are evaluated in order; the first match wins.  If no rule matches
    the *default_allow* flag is used.
    """
    result = AccessResult()
    for path in paths:
        decision = default_allow
        matched_rule: Optional[AccessRule] = None
        for rule in rules:
            if rule.matches(namespace, path):
                decision = rule.allow
                matched_rule = rule
                break

        if not decision:
            reason = (
                f"denied by rule '{matched_rule.namespace}:{matched_rule.path}'"
                if matched_rule
                else "no matching allow rule"
            )
            result.violations.append(AccessViolation(namespace, path, reason))
    return result
