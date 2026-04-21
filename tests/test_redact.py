"""Tests for vaultpatch.redact."""

from __future__ import annotations

import pytest

from vaultpatch.diff import SecretDiff
from vaultpatch.redact import (
    RedactConfig,
    _REDACTED,
    redact_diff,
    redact_diffs,
    redact_value,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _diff(key: str, old: str | None = "old", new: str | None = "new") -> SecretDiff:
    return SecretDiff(path="secret/app", key=key, old_value=old, new_value=new)


# ---------------------------------------------------------------------------
# RedactConfig.is_sensitive
# ---------------------------------------------------------------------------

def test_default_patterns_match_password():
    cfg = RedactConfig()
    assert cfg.is_sensitive("db_password") is True


def test_default_patterns_match_token():
    cfg = RedactConfig()
    assert cfg.is_sensitive("auth_token") is True


def test_non_sensitive_key_not_matched():
    cfg = RedactConfig()
    assert cfg.is_sensitive("username") is False


def test_extra_patterns_extend_defaults():
    cfg = RedactConfig(extra_patterns=["pin"])
    assert cfg.is_sensitive("user_pin") is True


def test_redact_all_flag_masks_any_key():
    cfg = RedactConfig(redact_all=True)
    assert cfg.is_sensitive("totally_harmless_key") is True


# ---------------------------------------------------------------------------
# redact_value
# ---------------------------------------------------------------------------

def test_redact_value_masks_sensitive():
    cfg = RedactConfig()
    assert redact_value("s3cr3t", "api_key", cfg) == _REDACTED


def test_redact_value_passes_through_safe_key():
    cfg = RedactConfig()
    assert redact_value("visible", "region", cfg) == "visible"


def test_redact_value_none_stays_none():
    cfg = RedactConfig()
    assert redact_value(None, "password", cfg) is None


# ---------------------------------------------------------------------------
# redact_diff
# ---------------------------------------------------------------------------

def test_redact_diff_masks_both_values_for_sensitive_key():
    cfg = RedactConfig()
    result = redact_diff(_diff("db_password", "old_pass", "new_pass"), cfg)
    assert result.old_value == _REDACTED
    assert result.new_value == _REDACTED


def test_redact_diff_preserves_path_and_key():
    cfg = RedactConfig()
    result = redact_diff(_diff("db_password"), cfg)
    assert result.path == "secret/app"
    assert result.key == "db_password"


def test_redact_diff_leaves_safe_key_unchanged():
    cfg = RedactConfig()
    result = redact_diff(_diff("environment", "prod", "staging"), cfg)
    assert result.old_value == "prod"
    assert result.new_value == "staging"


# ---------------------------------------------------------------------------
# redact_diffs
# ---------------------------------------------------------------------------

def test_redact_diffs_processes_list():
    diffs = [
        _diff("secret_key", "a", "b"),
        _diff("region", "us-east-1", "eu-west-1"),
    ]
    results = redact_diffs(diffs)
    assert results[0].new_value == _REDACTED
    assert results[1].new_value == "eu-west-1"


def test_redact_diffs_uses_default_config_when_none_given():
    diffs = [_diff("password", "hunter2", "hunter3")]
    results = redact_diffs(diffs)
    assert results[0].old_value == _REDACTED
