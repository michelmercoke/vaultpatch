"""Tests for vaultpatch/pin.py"""
import pytest
from pathlib import Path
from vaultpatch.pin import (
    PinEntry,
    PinStore,
    save_pins,
    load_pins,
    check_pin,
    PIN_FILE_VERSION,
)


@pytest.fixture
def tmp_pin(tmp_path) -> Path:
    return tmp_path / "pins.json"


def _entry(path="secret/app", namespace="dev", version=3, note="") -> PinEntry:
    return PinEntry(path=path, namespace=namespace, version=version, note=note)


def test_store_set_and_get():
    store = PinStore()
    e = _entry()
    store.set(e)
    result = store.get("dev", "secret/app")
    assert result is not None
    assert result.version == 3


def test_store_get_missing_returns_none():
    store = PinStore()
    assert store.get("dev", "secret/missing") is None


def test_store_remove_existing():
    store = PinStore()
    store.set(_entry())
    removed = store.remove("dev", "secret/app")
    assert removed is True
    assert store.get("dev", "secret/app") is None


def test_store_remove_missing_returns_false():
    store = PinStore()
    assert store.remove("dev", "secret/ghost") is False


def test_store_all_entries():
    store = PinStore()
    store.set(_entry(path="a"))
    store.set(_entry(path="b"))
    assert len(store.all_entries()) == 2


def test_save_and_load_roundtrip(tmp_pin):
    store = PinStore()
    store.set(_entry(note="pinned for release"))
    save_pins(store, tmp_pin)
    loaded = load_pins(tmp_pin)
    result = loaded.get("dev", "secret/app")
    assert result is not None
    assert result.version == 3
    assert result.note == "pinned for release"


def test_load_missing_file_raises(tmp_pin):
    with pytest.raises(FileNotFoundError):
        load_pins(tmp_pin)


def test_load_wrong_version_raises(tmp_pin):
    tmp_pin.write_text('{"version": 99, "pins": []}')
    with pytest.raises(ValueError, match="Unsupported pin file version"):
        load_pins(tmp_pin)


def test_check_pin_passes_correct_version():
    store = PinStore()
    store.set(_entry(version=5))
    assert check_pin(store, "dev", "secret/app", actual_version=5) is None


def test_check_pin_fails_wrong_version():
    store = PinStore()
    store.set(_entry(version=5))
    msg = check_pin(store, "dev", "secret/app", actual_version=7)
    assert msg is not None
    assert "pinned=5" in msg
    assert "actual=7" in msg


def test_check_pin_no_entry_returns_none():
    store = PinStore()
    assert check_pin(store, "prod", "secret/untracked", actual_version=1) is None
