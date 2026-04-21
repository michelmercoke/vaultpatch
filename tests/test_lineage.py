"""Tests for vaultpatch.lineage."""
import json
from pathlib import Path

import pytest

from vaultpatch.lineage import (
    LineageEntry,
    LineageRecord,
    build_entry,
    load_lineage,
    save_lineage,
)


@pytest.fixture()
def tmp_lineage(tmp_path: Path) -> Path:
    return tmp_path / "lineage.json"


def _entry(**kwargs) -> LineageEntry:
    defaults = dict(
        path="secret/app/db",
        source_namespace="staging",
        target_namespace="production",
        promoted_at="2024-01-01T00:00:00+00:00",
        promoted_by="alice",
    )
    defaults.update(kwargs)
    return LineageEntry(**defaults)


def test_build_entry_captures_fields():
    entry = build_entry(
        path="secret/app/api",
        source_namespace="dev",
        target_namespace="staging",
        promoted_by="bob",
    )
    assert entry.path == "secret/app/api"
    assert entry.source_namespace == "dev"
    assert entry.target_namespace == "staging"
    assert entry.promoted_by == "bob"
    assert entry.promoted_at  # non-empty timestamp


def test_build_entry_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("USER", "ci-bot")
    entry = build_entry("secret/x", "a", "b")
    assert entry.promoted_by == "ci-bot"


def test_record_add_and_for_path():
    record = LineageRecord()
    e1 = _entry(path="secret/app/db")
    e2 = _entry(path="secret/app/cache")
    record.add(e1)
    record.add(e2)
    assert len(record.for_path("secret/app/db")) == 1
    assert len(record.for_path("secret/app/cache")) == 1
    assert record.for_path("secret/missing") == []


def test_save_creates_file(tmp_lineage):
    record = LineageRecord()
    record.add(_entry())
    save_lineage(record, tmp_lineage)
    assert tmp_lineage.exists()


def test_save_load_roundtrip(tmp_lineage):
    record = LineageRecord()
    record.add(_entry(path="secret/roundtrip", promoted_by="eve"))
    save_lineage(record, tmp_lineage)
    loaded = load_lineage(tmp_lineage)
    assert len(loaded.entries) == 1
    assert loaded.entries[0].path == "secret/roundtrip"
    assert loaded.entries[0].promoted_by == "eve"


def test_load_missing_returns_empty(tmp_lineage):
    record = load_lineage(tmp_lineage)
    assert record.entries == []


def test_load_wrong_version_raises(tmp_lineage):
    tmp_lineage.write_text(json.dumps({"version": 99, "entries": []}))
    with pytest.raises(ValueError, match="Unsupported lineage version"):
        load_lineage(tmp_lineage)


def test_to_dict_structure():
    entry = _entry()
    d = entry.to_dict()
    assert set(d.keys()) == {
        "path", "source_namespace", "target_namespace",
        "promoted_at", "promoted_by",
    }
