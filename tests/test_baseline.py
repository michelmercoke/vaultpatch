"""Tests for vaultpatch.baseline module."""
import json
import pytest
from pathlib import Path
from datetime import datetime, timezone

from vaultpatch.baseline import (
    BaselineEntry,
    BaselineStore,
    save_baseline,
    load_baseline,
    baseline_key,
    BASELINE_VERSION,
)


@pytest.fixture
def tmp_baseline(tmp_path):
    return tmp_path / "baseline.json"


def _entry(namespace="prod", path="secret/db", secrets=None, label=None):
    return BaselineEntry(
        namespace=namespace,
        path=path,
        secrets=secrets or {"password": "s3cr3t"},
        label=label,
    )


def test_entry_to_dict_includes_all_fields():
    e = _entry(label="v1")
    d = e.to_dict()
    assert d["namespace"] == "prod"
    assert d["path"] == "secret/db"
    assert d["secrets"] == {"password": "s3cr3t"}
    assert d["label"] == "v1"
    assert "captured_at" in d


def test_store_set_and_get():
    store = BaselineStore()
    e = _entry()
    store.set(e)
    result = store.get("prod", "secret/db")
    assert result is e


def test_store_get_missing_returns_none():
    store = BaselineStore()
    assert store.get("prod", "secret/missing") is None


def test_store_remove_existing():
    store = BaselineStore()
    store.set(_entry())
    removed = store.remove("prod", "secret/db")
    assert removed is True
    assert store.get("prod", "secret/db") is None


def test_store_remove_missing_returns_false():
    store = BaselineStore()
    assert store.remove("prod", "secret/nope") is False


def test_store_all_returns_all_entries():
    store = BaselineStore()
    store.set(_entry(path="a"))
    store.set(_entry(path="b"))
    assert len(store.all()) == 2


def test_save_and_load_roundtrip(tmp_baseline):
    store = BaselineStore()
    store.set(_entry(label="base"))
    save_baseline(store, tmp_baseline)
    loaded = load_baseline(tmp_baseline)
    e = loaded.get("prod", "secret/db")
    assert e is not None
    assert e.label == "base"
    assert e.secrets == {"password": "s3cr3t"}


def test_load_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_baseline(tmp_path / "missing.json")


def test_load_wrong_version_raises(tmp_baseline):
    tmp_baseline.write_text(json.dumps({"version": 99, "entries": []}))
    with pytest.raises(ValueError, match="Unsupported baseline version"):
        load_baseline(tmp_baseline)


def test_save_creates_parent_dirs(tmp_path):
    deep = tmp_path / "a" / "b" / "baseline.json"
    store = BaselineStore()
    store.set(_entry())
    save_baseline(store, deep)
    assert deep.exists()


def test_baseline_key_format():
    assert baseline_key("prod", "secret/db") == "prod::secret/db"
