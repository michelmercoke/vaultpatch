"""Scope enforcement: restrict operations to allowed namespace/path patterns."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import List, Optional


@dataclass
class ScopeViolation:
    namespace: str
    path: str
    reason: str

    def __str__(self) -> str:
        return f"[{self.namespace}] {self.path}: {self.reason}"


@dataclass
class ScopeResult:
    violations: List[ScopeViolation] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0


@dataclass
class ScopeConfig:
    allowed_namespaces: List[str] = field(default_factory=list)  # glob patterns
    allowed_paths: List[str] = field(default_factory=list)        # glob patterns
    deny_message: str = "outside permitted scope"

    @classmethod
    def from_dict(cls, data: dict) -> "ScopeConfig":
        return cls(
            allowed_namespaces=data.get("allowed_namespaces", []),
            allowed_paths=data.get("allowed_paths", []),
            deny_message=data.get("deny_message", "outside permitted scope"),
        )

    def _namespace_allowed(self, namespace: str) -> bool:
        if not self.allowed_namespaces:
            return True
        return any(fnmatch(namespace, pat) for pat in self.allowed_namespaces)

    def _path_allowed(self, path: str) -> bool:
        if not self.allowed_paths:
            return True
        return any(fnmatch(path, pat) for pat in self.allowed_paths)


def check_scope(
    config: ScopeConfig,
    namespace: str,
    paths: List[str],
) -> ScopeResult:
    """Return a ScopeResult listing any paths that fall outside the allowed scope."""
    result = ScopeResult()
    if not config._namespace_allowed(namespace):
        for path in paths:
            result.violations.append(
                ScopeViolation(namespace, path, f"namespace '{namespace}' {config.deny_message}")
            )
        return result

    for path in paths:
        if not config._path_allowed(path):
            result.violations.append(
                ScopeViolation(namespace, path, f"path '{path}' {config.deny_message}")
            )
    return result
