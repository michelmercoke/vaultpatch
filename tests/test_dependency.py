"""Tests for vaultpatch.dependency."""
from __future__ import annotations

import pytest

from vaultpatch.dependency import (
    DependencyResult,
    DependencyViolation,
    resolve_dependencies,
)


def test_no_deps_returns_sorted_order():
    paths = ["secret/c", "secret/a", "secret/b"]
    result = resolve_dependencies(paths, {})
    assert result.ordered == ["secret/a", "secret/b", "secret/c"]
    assert not result.has_violations


def test_single_dependency_respected():
    paths = ["secret/app", "secret/db"]
    # app depends on db → db must come first
    deps = {"secret/app": ["secret/db"]}
    result = resolve_dependencies(paths, deps)
    assert result.ordered.index("secret/db") < result.ordered.index("secret/app")
    assert not result.has_violations


def test_chain_dependency_order():
    paths = ["a", "b", "c"]
    deps = {"b": ["a"], "c": ["b"]}
    result = resolve_dependencies(paths, deps)
    assert result.ordered == ["a", "b", "c"]


def test_cycle_detected_returns_violation():
    paths = ["x", "y"]
    deps = {"x": ["y"], "y": ["x"]}
    result = resolve_dependencies(paths, deps)
    assert result.has_violations
    reasons = [v.reason for v in result.violations]
    assert any("circular" in r for r in reasons)
    # Falls back to original path list (no crash)
    assert set(result.ordered) == {"x", "y"}


def test_unknown_dependency_path_records_violation():
    paths = ["secret/app"]
    deps = {"secret/app": ["secret/missing"]}
    result = resolve_dependencies(paths, deps)
    assert result.has_violations
    v = result.violations[0]
    assert v.path == "secret/app"
    assert v.depends_on == "secret/missing"
    assert "not present" in v.reason


def test_multiple_prerequisites():
    paths = ["web", "cache", "db"]
    deps = {"web": ["cache", "db"]}
    result = resolve_dependencies(paths, deps)
    web_idx = result.ordered.index("web")
    assert result.ordered.index("cache") < web_idx
    assert result.ordered.index("db") < web_idx


def test_violation_str():
    v = DependencyViolation(path="a", depends_on="b", reason="not found")
    assert "a" in str(v)
    assert "b" in str(v)
    assert "not found" in str(v)


def test_result_has_violations_false_when_empty():
    r = DependencyResult(ordered=[])
    assert not r.has_violations


def test_result_has_violations_true_when_present():
    v = DependencyViolation(path="x", depends_on="y", reason="cycle")
    r = DependencyResult(ordered=[], violations=[v])
    assert r.has_violations
