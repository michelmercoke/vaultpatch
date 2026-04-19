"""Tests for vaultpatch.snapshot."""
import json
import pytest
from pathlib import Path

from vaultpatch.snapshot import save_snapshot, load_snapshot, snapshot_key, SNAPSHOT_VERSION


@pytest.fixture
def tmp_snap(tmp_path):
    return tmp_path / "snap.json"


def test_save_creates_file(tmp_snap):
    save_snapshot(tmp_snap, {"ns/db": {"pass": "s3cr3t"}})
    assert tmp_snap.exists()


def test_save_load_roundtrip(tmp_snap):
    data = {"prod/db": {"user": "admin", "pass": "x"}, "prod/api": {"key": "abc"}}
    save_snapshot(tmp_snap, data)
    loaded = load_snapshot(tmp_snap)
    assert loaded == data


def test_load_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_snapshot(tmp_path / "nope.json")


def test_load_wrong_version_raises(tmp_snap):
    tmp_snap.write_text(json.dumps({"version": 99, "secrets": {}}))
    with pytest.raises(ValueError, match="Unsupported snapshot version"):
        load_snapshot(tmp_snap)


def test_snapshot_key_format():
    assert snapshot_key("prod", "db/creds") == "prod/db/creds"


def test_saved_version_field(tmp_snap):
    save_snapshot(tmp_snap, {})
    raw = json.loads(tmp_snap.read_text())
    assert raw["version"] == SNAPSHOT_VERSION
