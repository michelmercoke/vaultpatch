"""Tests for vaultpatch.signal."""
from __future__ import annotations

import pytest

from vaultpatch.diff import SecretDiff
from vaultpatch.signal import (
    SignalConfig,
    SignalResult,
    SignalViolation,
    check_signals,
)


def _diff(key: str, new_value: str, old_value: str = "old") -> SecretDiff:
    return SecretDiff(key=key, old_value=old_value, new_value=new_value)


# ---------------------------------------------------------------------------
# SignalConfig
# ---------------------------------------------------------------------------

def test_from_dict_defaults():
    cfg = SignalConfig.from_dict({})
    assert cfg.extra_patterns == []
    assert cfg.ignore_keys == []


def test_from_dict_custom():
    cfg = SignalConfig.from_dict(
        {"extra_patterns": [r"^test$"], "ignore_keys": ["irrelevant"]}
    )
    assert r"^test$" in cfg.extra_patterns
    assert "irrelevant" in cfg.ignore_keys


# ---------------------------------------------------------------------------
# check_signals – default patterns
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_value", [
    "changeme",
    "password",
    "secret",
    "todo",
    "FIXME",
    "replace-me",
    "<MY_SECRET>",
    "${MY_VAR}",
    "0000",
])
def test_default_patterns_trigger_violation(bad_value):
    diffs = [_diff("api_key", bad_value)]
    result = check_signals("ns/path", diffs)
    assert result.has_violations
    assert result.violations[0].key == "api_key"


def test_clean_value_produces_no_violation():
    diffs = [_diff("api_key", "xK9#mP2$qL7vR")]
    result = check_signals("ns/path", diffs)
    assert not result.has_violations


def test_removed_diff_is_skipped():
    diff = SecretDiff(key="api_key", old_value="changeme", new_value=None)
    result = check_signals("ns/path", [diff])
    assert not result.has_violations


def test_ignored_key_skipped():
    cfg = SignalConfig(ignore_keys=["api_key"])
    diffs = [_diff("api_key", "changeme")]
    result = check_signals("ns/path", diffs, cfg)
    assert not result.has_violations


def test_extra_pattern_triggers_violation():
    cfg = SignalConfig(extra_patterns=[r"^notallowed$"])
    diffs = [_diff("token", "notallowed")]
    result = check_signals("ns/path", diffs, cfg)
    assert result.has_violations
    assert "notallowed" in result.violations[0].pattern


def test_only_one_violation_per_key():
    """Even if multiple patterns match, only one violation per key."""
    cfg = SignalConfig(extra_patterns=[r"^changeme$"])
    diffs = [_diff("key", "changeme")]
    result = check_signals("ns/path", diffs, cfg)
    assert len(result.violations) == 1


def test_violation_str_contains_path_and_key():
    v = SignalViolation(path="prod/db", key="pass", pattern=r"^changeme$", value_snippet="changeme")
    s = str(v)
    assert "prod/db" in s
    assert "pass" in s
    assert "changeme" in s


def test_multiple_keys_each_get_violation():
    diffs = [
        _diff("key1", "changeme"),
        _diff("key2", "password"),
        _diff("key3", "xK9#mP2$qL7vR"),
    ]
    result = check_signals("ns/path", diffs)
    assert len(result.violations) == 2
    keys = {v.key for v in result.violations}
    assert keys == {"key1", "key2"}
