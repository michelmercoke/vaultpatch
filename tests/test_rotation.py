"""Tests for vaultpatch.rotation."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from vaultpatch.rotation import RotationEntry, RotationStore, RotationViolation

_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ts(dt: datetime) -> str:
    return dt.strftime(_FMT)


# --- RotationEntry ---

def test_entry_not_overdue_when_recent():
    now = _now()
    entry = RotationEntry(path="ns/secret", rotated_at=_ts(now - timedelta(days=10)), max_age_days=30)
    assert not entry.is_overdue(now)


def test_entry_is_overdue_when_old():
    now = _now()
    entry = RotationEntry(path="ns/secret", rotated_at=_ts(now - timedelta(days=40)), max_age_days=30)
    assert entry.is_overdue(now)


def test_entry_days_overdue_correct():
    now = _now()
    entry = RotationEntry(path="ns/secret", rotated_at=_ts(now - timedelta(days=35)), max_age_days=30)
    assert entry.days_overdue(now) == 5


def test_entry_days_overdue_zero_when_not_overdue():
    now = _now()
    entry = RotationEntry(path="ns/secret", rotated_at=_ts(now - timedelta(days=5)), max_age_days=30)
    assert entry.days_overdue(now) == 0


def test_entry_to_dict_roundtrip():
    now = _now()
    entry = RotationEntry(path="ns/secret", rotated_at=_ts(now), max_age_days=90)
    d = entry.to_dict()
    restored = RotationEntry(**d)
    assert restored.path == entry.path
    assert restored.max_age_days == entry.max_age_days


# --- RotationStore ---

def test_store_record_and_get():
    store = RotationStore()
    now = _now()
    store.record("ns/db", max_age_days=60, now=now)
    entry = store.get("ns/db")
    assert entry is not None
    assert entry.max_age_days == 60


def test_store_check_no_violations():
    store = RotationStore()
    now = _now()
    store.record("ns/db", max_age_days=60, now=now)
    result = store.check(["ns/db"], now=now)
    assert not result.has_violations
    assert not result.warnings


def test_store_check_detects_overdue():
    store = RotationStore()
    past = _now() - timedelta(days=100)
    store.record("ns/db", max_age_days=60, now=past)
    result = store.check(["ns/db"])
    assert result.has_violations
    assert result.violations[0].path == "ns/db"


def test_store_check_warns_on_missing_path():
    store = RotationStore()
    result = store.check(["ns/unknown"])
    assert not result.has_violations
    assert any("ns/unknown" in w for w in result.warnings)


def test_store_save_and_load(tmp_path: Path):
    store = RotationStore()
    now = _now()
    store.record("ns/api_key", max_age_days=45, now=now)
    store_file = tmp_path / "rotation.json"
    store.save(store_file)
    loaded = RotationStore.load(store_file)
    entry = loaded.get("ns/api_key")
    assert entry is not None
    assert entry.max_age_days == 45


def test_store_load_wrong_version_raises(tmp_path: Path):
    store_file = tmp_path / "rotation.json"
    store_file.write_text(json.dumps({"version": 99, "entries": {}}))
    with pytest.raises(ValueError, match="Unsupported"):
        RotationStore.load(store_file)


def test_violation_str():
    v = RotationViolation(path="ns/key", days_overdue=7)
    assert "ns/key" in str(v)
    assert "7" in str(v)
