"""Tests for vaultpatch.cooldown and vaultpatch.cooldown_hook."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from vaultpatch.cooldown import CooldownEntry, CooldownStore
from vaultpatch.cooldown_hook import (
    abort_on_cooldown,
    check_cooldowns,
    record_applied,
)


@pytest.fixture
def tmp_store(tmp_path) -> Path:
    return tmp_path / "cooldown.json"


# --- CooldownEntry ---

def test_entry_is_active_within_window():
    now = datetime.now(timezone.utc)
    entry = CooldownEntry(
        path="secret/foo",
        namespace="dev",
        applied_at=now.isoformat(),
        cooldown_seconds=300,
    )
    assert entry.is_active(now + timedelta(seconds=100)) is True


def test_entry_is_inactive_after_window():
    now = datetime.now(timezone.utc)
    entry = CooldownEntry(
        path="secret/foo",
        namespace="dev",
        applied_at=(now - timedelta(seconds=400)).isoformat(),
        cooldown_seconds=300,
    )
    assert entry.is_active(now) is False


def test_entry_to_dict_roundtrip():
    now = datetime.now(timezone.utc)
    entry = CooldownEntry(
        path="secret/bar",
        namespace="prod",
        applied_at=now.isoformat(),
        cooldown_seconds=60,
    )
    d = entry.to_dict()
    restored = CooldownEntry(**d)
    assert restored.path == entry.path
    assert restored.cooldown_seconds == entry.cooldown_seconds


# --- CooldownStore ---

def test_store_record_and_get():
    store = CooldownStore()
    store.record("dev", "secret/foo", cooldown_seconds=120)
    entry = store.get("dev", "secret/foo")
    assert entry is not None
    assert entry.path == "secret/foo"


def test_store_is_blocked_active():
    store = CooldownStore()
    store.record("dev", "secret/foo", cooldown_seconds=300)
    assert store.is_blocked("dev", "secret/foo") is True


def test_store_is_not_blocked_expired():
    store = CooldownStore()
    store.record("dev", "secret/foo", cooldown_seconds=1)
    future = datetime.now(timezone.utc) + timedelta(seconds=10)
    assert store.is_blocked("dev", "secret/foo", now=future) is False


def test_store_missing_path_not_blocked():
    store = CooldownStore()
    assert store.is_blocked("dev", "secret/missing") is False


def test_store_save_and_load(tmp_store):
    store = CooldownStore()
    store.record("prod", "secret/db", cooldown_seconds=600)
    store.save(tmp_store)
    loaded = CooldownStore.load(tmp_store)
    assert loaded.is_blocked("prod", "secret/db") is True


def test_store_load_missing_returns_empty(tmp_store):
    store = CooldownStore.load(tmp_store)
    assert store.all_entries() == []


# --- cooldown_hook ---

def test_check_cooldowns_returns_blocked(capsys):
    store = CooldownStore()
    store.record("dev", "secret/x", cooldown_seconds=300)
    blocked = check_cooldowns("dev", ["secret/x", "secret/y"], store, dry_run=True)
    assert blocked == ["secret/x"]


def test_check_cooldowns_empty_when_none_blocked():
    store = CooldownStore()
    blocked = check_cooldowns("dev", ["secret/z"], store)
    assert blocked == []


def test_abort_on_cooldown_raises_system_exit():
    with pytest.raises(SystemExit):
        abort_on_cooldown(["secret/x"], dry_run=False)


def test_abort_on_cooldown_dry_run_does_not_raise():
    abort_on_cooldown(["secret/x"], dry_run=True)  # should not raise


def test_record_applied_sets_cooldown():
    store = CooldownStore()
    record_applied("staging", ["secret/a", "secret/b"], store, cooldown_seconds=120)
    assert store.is_blocked("staging", "secret/a") is True
    assert store.is_blocked("staging", "secret/b") is True
