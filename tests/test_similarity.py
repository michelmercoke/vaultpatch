"""Tests for vaultpatch.similarity."""
from __future__ import annotations

import pytest

from vaultpatch.similarity import (
    SimilarityConfig,
    SimilarityViolation,
    check_similarity,
)


DEFAULT_CFG = SimilarityConfig(threshold=0.85)


def test_identical_values_produce_violation():
    secrets = {
        "ns/path/a": {"password": "s3cr3t!"},
        "ns/path/b": {"password": "s3cr3t!"},
    }
    result = check_similarity(secrets, DEFAULT_CFG)
    assert result.has_violations
    assert result.violations[0].ratio == pytest.approx(1.0)


def test_very_different_values_do_not_trigger():
    secrets = {
        "ns/path/a": {"password": "aaaaaa"},
        "ns/path/b": {"password": "zzzzzzzzzzzzzzzzzzz"},
    }
    result = check_similarity(secrets, DEFAULT_CFG)
    assert not result.has_violations


def test_checked_count_is_correct():
    secrets = {
        "ns/a": {"k1": "value1", "k2": "value2"},
        "ns/b": {"k3": "value3"},
    }
    result = check_similarity(secrets, DEFAULT_CFG)
    # 3 items -> 3 pairs
    assert result.checked == 3


def test_ignore_keys_are_skipped():
    cfg = SimilarityConfig(threshold=0.85, ignore_keys=["token"])
    secrets = {
        "ns/a": {"token": "identical_secret"},
        "ns/b": {"token": "identical_secret"},
    }
    result = check_similarity(secrets, cfg)
    assert not result.has_violations
    assert result.checked == 0


def test_empty_value_skipped():
    secrets = {
        "ns/a": {"key": ""},
        "ns/b": {"key": ""},
    }
    result = check_similarity(secrets, DEFAULT_CFG)
    assert result.checked == 0


def test_violation_str_contains_paths():
    v = SimilarityViolation(
        path_a="ns/a", key_a="pw", path_b="ns/b", key_b="pw", ratio=0.95
    )
    s = str(v)
    assert "ns/a" in s
    assert "ns/b" in s
    assert "0.95" in s


def test_config_from_dict_defaults():
    cfg = SimilarityConfig.from_dict({})
    assert cfg.threshold == pytest.approx(0.85)
    assert cfg.ignore_keys == []


def test_config_from_dict_custom():
    cfg = SimilarityConfig.from_dict({"threshold": 0.7, "ignore_keys": ["api_key"]})
    assert cfg.threshold == pytest.approx(0.7)
    assert "api_key" in cfg.ignore_keys


def test_threshold_boundary_not_triggered_below():
    cfg = SimilarityConfig(threshold=0.99)
    secrets = {
        "ns/a": {"pw": "password123"},
        "ns/b": {"pw": "password124"},
    }
    result = check_similarity(secrets, cfg)
    assert not result.has_violations
