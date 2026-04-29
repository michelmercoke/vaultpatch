"""Tests for vaultpatch.anomaly."""
import pytest

from vaultpatch.anomaly import AnomalyConfig, AnomalyViolation, check_anomalies
from vaultpatch.diff import SecretDiff


def _diff(key: str, old: str | None, new: str | None) -> SecretDiff:
    return SecretDiff(key=key, old_value=old, new_value=new)


@pytest.fixture
def cfg() -> AnomalyConfig:
    return AnomalyConfig(min_length=4, max_length=20)


def test_clean_value_passes(cfg):
    diffs = [_diff("api_key", None, "SuperSecure!99")]
    result = check_anomalies("ns/path", diffs, cfg)
    assert not result.has_violations


def test_too_short_produces_violation(cfg):
    diffs = [_diff("token", None, "abc")]
    result = check_anomalies("ns/path", diffs, cfg)
    assert result.has_violations
    assert any("too short" in str(v) for v in result.violations)


def test_too_long_produces_violation(cfg):
    diffs = [_diff("token", None, "x" * 25)]
    result = check_anomalies("ns/path", diffs, cfg)
    assert result.has_violations
    assert any("too long" in str(v) for v in result.violations)


def test_disallowed_pattern_produces_violation(cfg):
    diffs = [_diff("password", None, "changeme")]
    result = check_anomalies("ns/path", diffs, cfg)
    assert result.has_violations
    assert any("disallowed pattern" in str(v) for v in result.violations)


def test_removed_diff_is_skipped(cfg):
    diffs = [_diff("token", "old", None)]
    result = check_anomalies("ns/path", diffs, cfg)
    assert not result.has_violations


def test_non_ascii_produces_violation(cfg):
    diffs = [_diff("secret", None, "vàlüé123")]
    result = check_anomalies("ns/path", diffs, cfg)
    assert result.has_violations
    assert any("non-ASCII" in str(v) for v in result.violations)


def test_non_ascii_allowed_when_disabled():
    cfg = AnomalyConfig(min_length=1, require_non_ascii_free=False)
    diffs = [_diff("k", None, "vàlüé")]
    result = check_anomalies("ns/path", diffs, cfg)
    assert not result.has_violations


def test_from_dict_defaults():
    cfg = AnomalyConfig.from_dict({})
    assert cfg.min_length == 8
    assert cfg.max_length == 4096
    assert cfg.require_non_ascii_free is True


def test_from_dict_custom():
    cfg = AnomalyConfig.from_dict({"min_length": 16, "max_length": 512})
    assert cfg.min_length == 16
    assert cfg.max_length == 512


def test_violation_str():
    v = AnomalyViolation(path="ns/p", key="k", reason="too short (2 < 8)")
    assert "ns/p" in str(v)
    assert "too short" in str(v)
