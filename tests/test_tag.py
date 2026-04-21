"""Tests for vaultpatch/tag.py — TagEntry, TagStore, save/load."""

from __future__ import annotations

import pytest

from vaultpatch.tag import TagEntry, TagStore, load_tags, save_tags


# ---------------------------------------------------------------------------
# TagEntry
# ---------------------------------------------------------------------------

def test_tag_entry_has_tag():
    e = TagEntry(path="secret/db", namespace="prod", tags=["critical", "db"])
    assert e.has_tag("critical")
    assert not e.has_tag("audit")


def test_tag_entry_add_tag_no_duplicate():
    e = TagEntry(path="secret/db", namespace="prod", tags=["critical"])
    e.add_tag("critical")
    assert e.tags.count("critical") == 1
    e.add_tag("audit")
    assert "audit" in e.tags


def test_tag_entry_remove_tag():
    e = TagEntry(path="secret/db", namespace="prod", tags=["critical", "db"])
    e.remove_tag("db")
    assert "db" not in e.tags
    assert "critical" in e.tags


def test_tag_entry_to_dict_sorted():
    e = TagEntry(path="p", namespace="ns", tags=["z", "a"])
    d = e.to_dict()
    assert d["tags"] == ["a", "z"]


# ---------------------------------------------------------------------------
# TagStore
# ---------------------------------------------------------------------------

def test_store_set_and_get():
    store = TagStore()
    store.set_tags("prod", "secret/db", ["critical"])
    entry = store.get("prod", "secret/db")
    assert entry is not None
    assert entry.has_tag("critical")


def test_store_get_missing_returns_none():
    store = TagStore()
    assert store.get("prod", "secret/missing") is None


def test_store_find_by_tag():
    store = TagStore()
    store.set_tags("prod", "secret/db", ["critical", "db"])
    store.set_tags("prod", "secret/api", ["api"])
    store.set_tags("staging", "secret/db", ["critical"])
    results = store.find_by_tag("critical")
    paths = [(r.namespace, r.path) for r in results]
    assert ("prod", "secret/db") in paths
    assert ("staging", "secret/db") in paths
    assert len([r for r in results if r.path == "secret/api"]) == 0


def test_store_all_entries():
    store = TagStore()
    store.set_tags("prod", "a", ["x"])
    store.set_tags("prod", "b", ["y"])
    assert len(store.all_entries()) == 2


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_save_load_roundtrip(tmp_path):
    fp = tmp_path / "tags.json"
    store = TagStore()
    store.set_tags("prod", "secret/db", ["critical", "db"])
    store.set_tags("staging", "secret/api", ["api"])
    save_tags(store, fp)
    loaded = load_tags(fp)
    entry = loaded.get("prod", "secret/db")
    assert entry is not None
    assert entry.has_tag("critical")
    assert loaded.get("staging", "secret/api").has_tag("api")


def test_load_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_tags(tmp_path / "nonexistent.json")


def test_load_wrong_version_raises(tmp_path):
    import json
    fp = tmp_path / "tags.json"
    fp.write_text(json.dumps({"version": 99, "entries": []}))
    with pytest.raises(ValueError, match="Unsupported"):
        load_tags(fp)
