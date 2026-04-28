"""Tests for vaultpatch/scope.py"""
import pytest

from vaultpatch.scope import ScopeConfig, ScopeViolation, check_scope


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cfg(
    namespaces=None,
    paths=None,
    deny_message="outside permitted scope",
) -> ScopeConfig:
    return ScopeConfig(
        allowed_namespaces=namespaces or [],
        allowed_paths=paths or [],
        deny_message=deny_message,
    )


# ---------------------------------------------------------------------------
# Namespace checks
# ---------------------------------------------------------------------------

def test_no_namespace_restriction_allows_any():
    cfg = _cfg(namespaces=[])
    result = check_scope(cfg, "prod", ["secret/db"])
    assert not result.has_violations


def test_exact_namespace_match_passes():
    cfg = _cfg(namespaces=["prod"])
    result = check_scope(cfg, "prod", ["secret/db"])
    assert not result.has_violations


def test_namespace_glob_match_passes():
    cfg = _cfg(namespaces=["prod-*"])
    result = check_scope(cfg, "prod-eu", ["secret/key"])
    assert not result.has_violations


def test_disallowed_namespace_produces_violation_per_path():
    cfg = _cfg(namespaces=["staging"])
    result = check_scope(cfg, "prod", ["secret/a", "secret/b"])
    assert result.has_violations
    assert len(result.violations) == 2
    assert all(v.namespace == "prod" for v in result.violations)


# ---------------------------------------------------------------------------
# Path checks
# ---------------------------------------------------------------------------

def test_no_path_restriction_allows_any():
    cfg = _cfg(paths=[])
    result = check_scope(cfg, "prod", ["secret/anything"])
    assert not result.has_violations


def test_exact_path_match_passes():
    cfg = _cfg(paths=["secret/db"])
    result = check_scope(cfg, "prod", ["secret/db"])
    assert not result.has_violations


def test_path_glob_match_passes():
    cfg = _cfg(paths=["secret/*"])
    result = check_scope(cfg, "prod", ["secret/db", "secret/api"])
    assert not result.has_violations


def test_disallowed_path_produces_violation():
    cfg = _cfg(paths=["secret/allowed"])
    result = check_scope(cfg, "prod", ["secret/forbidden"])
    assert result.has_violations
    assert result.violations[0].path == "secret/forbidden"


def test_mixed_paths_only_violating_flagged():
    cfg = _cfg(paths=["secret/ok"])
    result = check_scope(cfg, "prod", ["secret/ok", "secret/bad"])
    assert len(result.violations) == 1
    assert result.violations[0].path == "secret/bad"


# ---------------------------------------------------------------------------
# from_dict
# ---------------------------------------------------------------------------

def test_from_dict_defaults():
    cfg = ScopeConfig.from_dict({})
    assert cfg.allowed_namespaces == []
    assert cfg.allowed_paths == []
    assert cfg.deny_message == "outside permitted scope"


def test_from_dict_custom_values():
    cfg = ScopeConfig.from_dict(
        {"allowed_namespaces": ["prod"], "allowed_paths": ["secret/*"], "deny_message": "denied"}
    )
    assert cfg.allowed_namespaces == ["prod"]
    assert cfg.allowed_paths == ["secret/*"]
    assert cfg.deny_message == "denied"


# ---------------------------------------------------------------------------
# Violation str
# ---------------------------------------------------------------------------

def test_violation_str():
    v = ScopeViolation("prod", "secret/db", "outside permitted scope")
    assert "prod" in str(v)
    assert "secret/db" in str(v)
