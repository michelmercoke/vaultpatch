"""Tests for vaultpatch.fingerprint_store."""
import pytest
from pathlib import Path

from vaultpatch.fingerprint import build_fingerprint
from vaultpatch.fingerprint_store import (
    fingerprint_store_key,
    load_fingerprints,
    save_fingerprints,
)


@pytest.fixture
def tmp_store(tmp_path):
    return tmp_path


def _entry(path="secret/app", ns="dev", secrets=None):
    return build_fingerprint(path, ns, secrets or {"key": "val"})


def test_save_creates_file(tmp_store):
    store_file = tmp_store / "fp.json"
    save_fingerprints(store_file, [_entry()])
    assert store_file.exists()


def test_save_load_roundtrip(tmp_store):
    store_file = tmp_store / "fp.json"
    original = [_entry("secret/a", "prod", {"x": "1"}), _entry("secret/b", "prod", {"y": "2"})]
    save_fingerprints(store_file, original)
    loaded = load_fingerprints(store_file)
    assert len(loaded) == 2
    assert loaded[0].path == "secret/a"
    assert loaded[1].digest == original[1].digest


def test_load_missing_raises(tmp_store):
    with pytest.raises(FileNotFoundError):
        load_fingerprints(tmp_store / "nonexistent.json")


def test_load_wrong_version_raises(tmp_store):
    import json
    bad = tmp_store / "bad.json"
    bad.write_text(json.dumps({"version": 99, "entries": []}))
    with pytest.raises(ValueError, match="Unsupported"):
        load_fingerprints(bad)


def test_fingerprint_store_key_sanitises_slashes():
    key = fingerprint_store_key("org/team/dev")
    assert "/" not in key
    assert key.endswith(".json")


def test_save_creates_parent_dirs(tmp_store):
    nested = tmp_store / "a" / "b" / "fp.json"
    save_fingerprints(nested, [_entry()])
    assert nested.exists()
