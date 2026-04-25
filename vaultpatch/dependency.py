"""Dependency ordering for secret paths across namespaces.

Allows users to declare that one secret path must be applied before another,
enabling safe ordered rollouts when secrets reference each other.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DependencyViolation:
    path: str
    depends_on: str
    reason: str

    def __str__(self) -> str:
        return f"{self.path} depends on {self.depends_on}: {self.reason}"


@dataclass
class DependencyResult:
    ordered: List[str]
    violations: List[DependencyViolation] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)


def _topological_sort(
    paths: List[str], deps: Dict[str, List[str]]
) -> Optional[List[str]]:
    """Kahn's algorithm; returns None if a cycle is detected."""
    in_degree: Dict[str, int] = {p: 0 for p in paths}
    graph: Dict[str, List[str]] = {p: [] for p in paths}

    for path, predecessors in deps.items():
        if path not in in_degree:
            continue
        for pred in predecessors:
            if pred not in in_degree:
                continue
            graph[pred].append(path)
            in_degree[path] += 1

    queue = [p for p, d in in_degree.items() if d == 0]
    queue.sort()  # deterministic output
    result: List[str] = []

    while queue:
        node = queue.pop(0)
        result.append(node)
        for neighbour in sorted(graph[node]):
            in_degree[neighbour] -= 1
            if in_degree[neighbour] == 0:
                queue.append(neighbour)

    return result if len(result) == len(paths) else None


def resolve_dependencies(
    paths: List[str],
    deps: Dict[str, List[str]],
) -> DependencyResult:
    """Return a safe apply order for *paths* given dependency declarations.

    Args:
        paths: Secret paths that will be applied.
        deps:  Mapping of ``{path: [must_be_applied_before_path]}``,
               i.e. the values are *prerequisites* of the key.
    """
    violations: List[DependencyViolation] = []

    # Warn about declared dependencies that reference unknown paths.
    for path, predecessors in deps.items():
        for pred in predecessors:
            if pred not in paths:
                violations.append(
                    DependencyViolation(
                        path=path,
                        depends_on=pred,
                        reason="dependency path not present in apply set",
                    )
                )

    ordered = _topological_sort(paths, deps)
    if ordered is None:
        # Cycle detected — fall back to original order and record violation.
        violations.append(
            DependencyViolation(
                path="(cycle)",
                depends_on="(cycle)",
                reason="circular dependency detected; using original order",
            )
        )
        ordered = list(paths)

    return DependencyResult(ordered=ordered, violations=violations)
