"""Tests for vaultpatch.ratelimit."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from vaultpatch.ratelimit import (
    RateLimitConfig,
    RateLimitStore,
    RateLimitViolation,
    check_rate_limit,
)


@pytest.fixture
def tmp_store(tmp_path: Path) -> RateLimitStore:
    return RateLimitStore.load(tmp_path / "ratelimit.json")


def test_no_violation_when_within_limits(tmp_store: RateLimitStore) -> None:
    cfg = RateLimitConfig(max_writes_per_minute=10, max_writes_per_hour=100)
    for _ in range(5):
        tmp_store.record("ns/dev")
    result = check_rate_limit("ns/dev", cfg, tmp_store)
    assert not result.has_violations


def test_per_minute_violation(tmp_store: RateLimitStore) -> None:
    cfg = RateLimitConfig(max_writes_per_minute=3, max_writes_per_hour=100)
    for _ in range(3):
        tmp_store.record("ns/dev")
    result = check_rate_limit("ns/dev", cfg, tmp_store)
    assert result.has_violations
    assert any(v.window == "1 minute" for v in result.violations)


def test_per_hour_violation(tmp_store: RateLimitStore) -> None:
    cfg = RateLimitConfig(max_writes_per_minute=1000, max_writes_per_hour=5)
    for _ in range(5):
        tmp_store.record("ns/prod")
    result = check_rate_limit("ns/prod", cfg, tmp_store)
    assert result.has_violations
    assert any(v.window == "1 hour" for v in result.violations)


def test_violation_str() -> None:
    v = RateLimitViolation(namespace="ns/prod", window="1 minute", limit=10, actual=12)
    assert "ns/prod" in str(v)
    assert "1 minute" in str(v)
    assert "12" in str(v)


def test_store_save_and_load_roundtrip(tmp_path: Path) -> None:
    store_path = tmp_path / "rl.json"
    store = RateLimitStore.load(store_path)
    store.record("ns/dev")
    store.record("ns/dev")
    store.save()
    reloaded = RateLimitStore.load(store_path)
    assert reloaded.writes_in_window("ns/dev", 60) == 2


def test_prune_removes_old_entries(tmp_store: RateLimitStore) -> None:
    now = time.time()
    tmp_store._data["ns/dev"] = [now - 7200, now - 3601, now - 10]
    tmp_store.prune("ns/dev", max_age=3600)
    assert tmp_store.writes_in_window("ns/dev", 3600) == 1


def test_from_dict_defaults() -> None:
    cfg = RateLimitConfig.from_dict({})
    assert cfg.max_writes_per_minute == 60
    assert cfg.max_writes_per_hour == 500


def test_from_dict_custom() -> None:
    cfg = RateLimitConfig.from_dict({"max_writes_per_minute": 5, "max_writes_per_hour": 50})
    assert cfg.max_writes_per_minute == 5
    assert cfg.max_writes_per_hour == 50


def test_empty_namespace_no_violation(tmp_store: RateLimitStore) -> None:
    cfg = RateLimitConfig(max_writes_per_minute=10, max_writes_per_hour=100)
    result = check_rate_limit("ns/new", cfg, tmp_store)
    assert not result.has_violations
    assert result.namespace == "ns/new"
