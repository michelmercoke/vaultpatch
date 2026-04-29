"""Tests for vaultpatch.observe and vaultpatch.observe_hook."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vaultpatch.diff import SecretDiff
from vaultpatch.observe import ObserveEntry, ObserveStore, load_store, save_store
from vaultpatch.observe_hook import echo_all_observations, echo_hotspots, record_observations


@pytest.fixture
def tmp_store(tmp_path) -> Path:
    return tmp_path / "observe.json"


def _diff(key: str, old, new) -> SecretDiff:
    return SecretDiff(key=key, old_value=old, new_value=new)


# --- ObserveStore unit tests ---

def test_record_creates_entry():
    store = ObserveStore()
    entry = store.record("secret/db", "prod", ["password"])
    assert entry.path == "secret/db"
    assert entry.namespace == "prod"
    assert entry.change_count == 1
    assert "password" in entry.keys_changed


def test_record_increments_existing():
    store = ObserveStore()
    store.record("secret/db", "prod", ["password"])
    entry = store.record("secret/db", "prod", ["user"])
    assert entry.change_count == 2
    assert "password" in entry.keys_changed
    assert "user" in entry.keys_changed


def test_get_missing_returns_none():
    store = ObserveStore()
    assert store.get("nonexistent") is None


def test_hotspots_returns_top_n():
    store = ObserveStore()
    store.record("a", "ns", ["k"])
    store.record("b", "ns", ["k"])
    store.record("b", "ns", ["k"])
    store.record("b", "ns", ["k"])
    hotspots = store.hotspots(top_n=1)
    assert len(hotspots) == 1
    assert hotspots[0].path == "b"


def test_to_dict_roundtrip():
    store = ObserveStore()
    store.record("secret/x", "dev", ["token"])
    d = store.to_dict()
    assert "secret/x" in d
    assert d["secret/x"]["change_count"] == 1


# --- Persistence tests ---

def test_save_and_load_roundtrip(tmp_store):
    store = ObserveStore()
    store.record("secret/y", "staging", ["api_key"])
    save_store(store, tmp_store)
    loaded = load_store(tmp_store)
    entry = loaded.get("secret/y")
    assert entry is not None
    assert entry.change_count == 1
    assert entry.namespace == "staging"


def test_load_missing_file_returns_empty(tmp_store):
    store = load_store(tmp_store)
    assert store.all_entries() == []


# --- Hook tests ---

def test_record_observations_skips_unchanged(tmp_store):
    diffs = {"secret/z": [_diff("key", "same", "same")]}
    store = record_observations(diffs, "prod", store_path=tmp_store)
    assert store.get("secret/z") is None


def test_record_observations_records_changed(tmp_store):
    diffs = {"secret/z": [_diff("key", "old", "new")]}
    store = record_observations(diffs, "prod", store_path=tmp_store)
    assert store.get("secret/z") is not None


def test_echo_hotspots_empty(capsys):
    store = ObserveStore()
    echo_hotspots(store)
    out = capsys.readouterr().out
    assert "No observations" in out


def test_echo_all_observations_lists_paths(capsys):
    store = ObserveStore()
    store.record("secret/alpha", "ns", ["x"])
    echo_all_observations(store)
    out = capsys.readouterr().out
    assert "secret/alpha" in out
