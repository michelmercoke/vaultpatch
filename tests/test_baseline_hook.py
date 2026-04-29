"""Tests for vaultpatch.baseline_hook module."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from vaultpatch.baseline import BaselineEntry, BaselineStore, save_baseline
from vaultpatch.baseline_hook import (
    capture_baseline,
    merge_into_store,
    echo_baseline_summary,
    load_or_empty,
)
from vaultpatch.fetch import FetchResult


def _fetch_ok(secrets: dict) -> FetchResult:
    r = MagicMock(spec=FetchResult)
    r.success = True
    r.secrets = secrets
    return r


def _fetch_fail() -> FetchResult:
    r = MagicMock(spec=FetchResult)
    r.success = False
    r.secrets = {}
    return r


def test_capture_baseline_includes_successful_paths():
    results = {
        "secret/db": _fetch_ok({"host": "localhost"}),
        "secret/api": _fetch_ok({"key": "abc"}),
    }
    store = capture_baseline(results, namespace="prod")
    assert store.get("prod", "secret/db") is not None
    assert store.get("prod", "secret/api") is not None


def test_capture_baseline_excludes_failed_paths():
    results = {
        "secret/db": _fetch_ok({"host": "localhost"}),
        "secret/missing": _fetch_fail(),
    }
    store = capture_baseline(results, namespace="prod")
    assert store.get("prod", "secret/missing") is None


def test_capture_baseline_sets_label():
    results = {"secret/db": _fetch_ok({"x": "y"})}
    store = capture_baseline(results, namespace="prod", label="release-1")
    e = store.get("prod", "secret/db")
    assert e.label == "release-1"


def test_merge_into_store_overlays_entries():
    existing = BaselineStore()
    existing.set(BaselineEntry(namespace="prod", path="secret/a", secrets={"k": "old"}))

    incoming = BaselineStore()
    incoming.set(BaselineEntry(namespace="prod", path="secret/a", secrets={"k": "new"}))
    incoming.set(BaselineEntry(namespace="prod", path="secret/b", secrets={"x": "1"}))

    merged = merge_into_store(existing, incoming)
    assert merged.get("prod", "secret/a").secrets == {"k": "new"}
    assert merged.get("prod", "secret/b") is not None


def test_echo_baseline_summary_prints_count(capsys):
    store = BaselineStore()
    store.set(BaselineEntry(namespace="prod", path="secret/db", secrets={"a": "b"}))
    echo_baseline_summary(store)
    captured = capsys.readouterr()
    assert "1 path" in captured.out


def test_echo_baseline_summary_verbose(capsys):
    store = BaselineStore()
    store.set(BaselineEntry(namespace="prod", path="secret/db", secrets={"a": "b"}, label="v1"))
    echo_baseline_summary(store, verbose=True)
    captured = capsys.readouterr()
    assert "secret/db" in captured.out
    assert "[v1]" in captured.out


def test_load_or_empty_returns_empty_when_missing(tmp_path):
    store = load_or_empty(tmp_path / "nope.json")
    assert isinstance(store, BaselineStore)
    assert store.all() == []


def test_load_or_empty_loads_existing(tmp_path):
    p = tmp_path / "baseline.json"
    s = BaselineStore()
    s.set(BaselineEntry(namespace="prod", path="secret/x", secrets={"k": "v"}))
    save_baseline(s, p)
    loaded = load_or_empty(p)
    assert loaded.get("prod", "secret/x") is not None
