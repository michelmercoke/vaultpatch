"""Tests for vaultpatch.checkpoint."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vaultpatch.checkpoint import (
    CHECKPOINT_VERSION,
    Checkpoint,
    CheckpointEntry,
    create_checkpoint,
    list_checkpoints,
    load_checkpoint,
    save_checkpoint,
)


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path / "checkpoints"


def _entry(ns: str = "prod", path: str = "secret/app") -> CheckpointEntry:
    return CheckpointEntry(namespace=ns, path=path, secrets={"key": "val"})


# ---------------------------------------------------------------------------
# create_checkpoint
# ---------------------------------------------------------------------------

def test_create_checkpoint_sets_name() -> None:
    cp = create_checkpoint("release-1")
    assert cp.name == "release-1"


def test_create_checkpoint_has_no_entries() -> None:
    cp = create_checkpoint("empty")
    assert cp.entries == []


def test_create_checkpoint_has_timestamp() -> None:
    cp = create_checkpoint("ts")
    assert "T" in cp.created_at  # ISO-8601


# ---------------------------------------------------------------------------
# save / load round-trip
# ---------------------------------------------------------------------------

def test_save_creates_file(tmp_dir: Path) -> None:
    cp = create_checkpoint("snap1")
    cp.add(_entry())
    fp = save_checkpoint(cp, str(tmp_dir))
    assert fp.exists()


def test_save_load_roundtrip(tmp_dir: Path) -> None:
    cp = create_checkpoint("snap2")
    cp.add(_entry("staging", "secret/db"))
    save_checkpoint(cp, str(tmp_dir))

    loaded = load_checkpoint("snap2", str(tmp_dir))
    assert loaded.name == "snap2"
    assert len(loaded.entries) == 1
    assert loaded.entries[0].namespace == "staging"
    assert loaded.entries[0].secrets == {"key": "val"}


def test_load_missing_raises(tmp_dir: Path) -> None:
    with pytest.raises(FileNotFoundError, match="ghost"):
        load_checkpoint("ghost", str(tmp_dir))


def test_load_wrong_version_raises(tmp_dir: Path) -> None:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    bad = tmp_dir / "bad.checkpoint.json"
    bad.write_text(json.dumps({"version": 99, "name": "bad", "created_at": "x", "entries": []}))
    with pytest.raises(ValueError, match="Unsupported"):
        load_checkpoint("bad", str(tmp_dir))


# ---------------------------------------------------------------------------
# list_checkpoints
# ---------------------------------------------------------------------------

def test_list_checkpoints_empty(tmp_dir: Path) -> None:
    assert list_checkpoints(str(tmp_dir)) == []


def test_list_checkpoints_returns_names(tmp_dir: Path) -> None:
    for name in ("alpha", "beta", "gamma"):
        cp = create_checkpoint(name)
        save_checkpoint(cp, str(tmp_dir))
    assert list_checkpoints(str(tmp_dir)) == ["alpha", "beta", "gamma"]


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------

def test_checkpoint_to_dict_structure() -> None:
    cp = create_checkpoint("v1")
    cp.add(_entry())
    d = cp.to_dict()
    assert d["version"] == CHECKPOINT_VERSION
    assert d["name"] == "v1"
    assert len(d["entries"]) == 1
    assert d["entries"][0]["path"] == "secret/app"
