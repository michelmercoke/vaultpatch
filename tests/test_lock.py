"""Tests for vaultpatch.lock."""

import time
from pathlib import Path

import pytest

from vaultpatch.lock import acquire_lock, release_lock, _lock_path


@pytest.fixture
def lock_dir(tmp_path: Path) -> Path:
    return tmp_path / "locks"


def test_acquire_creates_lock_file(lock_dir):
    result = acquire_lock("dev/app", lock_dir=lock_dir)
    assert result.acquired
    assert result.lock_file.exists()


def test_acquire_records_namespace(lock_dir):
    result = acquire_lock("staging", lock_dir=lock_dir)
    assert result.namespace == "staging"


def test_double_acquire_fails(lock_dir):
    acquire_lock("prod", lock_dir=lock_dir)
    second = acquire_lock("prod", lock_dir=lock_dir)
    assert not second.acquired
    assert "Lock held" in second.error


def test_stale_lock_is_replaced(lock_dir, monkeypatch):
    lock_dir.mkdir(parents=True, exist_ok=True)
    path = _lock_path("prod", lock_dir)
    path.write_text("99999")
    # backdate mtime by 400s
    old_time = time.time() - 400
    import os
    os.utime(path, (old_time, old_time))

    result = acquire_lock("prod", lock_dir=lock_dir, ttl=300)
    assert result.acquired


def test_release_removes_file(lock_dir):
    acquire_lock("dev", lock_dir=lock_dir)
    released = release_lock("dev", lock_dir=lock_dir)
    assert released
    assert not _lock_path("dev", lock_dir).exists()


def test_release_missing_lock_returns_true(lock_dir):
    result = release_lock("nonexistent", lock_dir=lock_dir)
    assert result


def test_lock_file_contains_pid(lock_dir):
    import os
    acquire_lock("check-pid", lock_dir=lock_dir)
    path = _lock_path("check-pid", lock_dir)
    assert path.read_text() == str(os.getpid())


def test_namespace_slash_sanitised(lock_dir):
    acquire_lock("ns/with/slashes", lock_dir=lock_dir)
    path = _lock_path("ns/with/slashes", lock_dir)
    assert "/" not in path.name
