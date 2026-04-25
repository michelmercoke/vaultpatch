"""Tests for vaultpatch.immutable."""

import pytest

from vaultpatch.diff import SecretDiff
from vaultpatch.immutable import (
    ImmutableConfig,
    ImmutableResult,
    ImmutableViolation,
    check_immutable,
    summarise_immutable,
)


def _diff(
    key: str,
    old: str | None = "old",
    new: str | None = "new",
    path: str = "secret/app",
) -> SecretDiff:
    return SecretDiff(path=path, key=key, old_value=old, new_value=new)


@pytest.fixture
def cfg() -> ImmutableConfig:
    return ImmutableConfig(keys=["db_password", "api_*"])


# ---------------------------------------------------------------------------
# ImmutableConfig.is_immutable
# ---------------------------------------------------------------------------

def test_exact_key_is_immutable(cfg):
    assert cfg.is_immutable("db_password") is True


def test_wildcard_key_is_immutable(cfg):
    assert cfg.is_immutable("api_token") is True
    assert cfg.is_immutable("api_secret") is True


def test_non_immutable_key(cfg):
    assert cfg.is_immutable("log_level") is False


# ---------------------------------------------------------------------------
# check_immutable
# ---------------------------------------------------------------------------

def test_added_immutable_key_is_allowed(cfg):
    """First-time writes to immutable keys should not raise a violation."""
    d = _diff("db_password", old=None, new="s3cr3t")
    result = check_immutable([d], cfg)
    assert not result.has_violations


def test_changed_immutable_key_is_violation(cfg):
    d = _diff("db_password", old="old", new="new")
    result = check_immutable([d], cfg)
    assert result.has_violations
    assert result.violations[0].key == "db_password"
    assert result.violations[0].path == "secret/app"


def test_removed_immutable_key_is_violation(cfg):
    d = _diff("api_token", old="tok", new=None)
    result = check_immutable([d], cfg)
    assert result.has_violations


def test_changed_non_immutable_key_passes(cfg):
    d = _diff("log_level", old="info", new="debug")
    result = check_immutable([d], cfg)
    assert not result.has_violations


def test_multiple_diffs_collects_all_violations(cfg):
    diffs = [
        _diff("db_password", old="a", new="b"),
        _diff("api_key", old="x", new="y"),
        _diff("log_level", old="info", new="warn"),
    ]
    result = check_immutable(diffs, cfg)
    assert len(result.violations) == 2
    violated_keys = {v.key for v in result.violations}
    assert violated_keys == {"db_password", "api_key"}


# ---------------------------------------------------------------------------
# summarise_immutable
# ---------------------------------------------------------------------------

def test_summarise_no_violations():
    result = ImmutableResult()
    summary = summarise_immutable(result)
    assert "passed" in summary


def test_summarise_with_violations():
    result = ImmutableResult(
        violations=[ImmutableViolation(path="secret/app", key="db_password")]
    )
    summary = summarise_immutable(result)
    assert "immutable violations" in summary
    assert "db_password" in summary
