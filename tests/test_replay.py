"""Tests for vaultpatch.replay."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from vaultpatch.replay import replay_audit_log, summarise_replay, ReplayEntry


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    entries = [
        {
            "timestamp": "2024-06-01T10:00:00",
            "namespace": "prod",
            "path": "secret/db",
            "mode": "apply",
            "changes": [{"key": "password", "change_type": "changed"}],
            "operator": "alice",
        },
        {
            "timestamp": "2024-06-02T11:00:00",
            "namespace": "staging",
            "path": "secret/api",
            "mode": "apply",
            "changes": [{"key": "token", "change_type": "added"}],
            "operator": "bob",
        },
        {
            "timestamp": "2024-06-03T09:00:00",
            "namespace": "prod",
            "path": "secret/cache",
            "mode": "diff",
            "changes": [],
            "operator": "alice",
        },
    ]
    p = tmp_path / "audit.log"
    with p.open("w") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")
    return p


def test_replay_returns_all_entries(log_file: Path) -> None:
    result = replay_audit_log(log_file)
    assert result.success
    assert result.total == 3


def test_replay_filters_by_namespace(log_file: Path) -> None:
    result = replay_audit_log(log_file, namespace="prod")
    assert result.total == 2
    assert all(e.namespace == "prod" for e in result.entries)


def test_replay_filters_by_since(log_file: Path) -> None:
    result = replay_audit_log(log_file, since="2024-06-02T00:00:00")
    assert result.total == 2
    assert all(e.timestamp >= "2024-06-02T00:00:00" for e in result.entries)


def test_replay_filters_by_until(log_file: Path) -> None:
    result = replay_audit_log(log_file, until="2024-06-01T23:59:59")
    assert result.total == 1
    assert result.entries[0].path == "secret/db"


def test_replay_filters_by_path_prefix(log_file: Path) -> None:
    result = replay_audit_log(log_file, path_prefix="secret/db")
    assert result.total == 1
    assert result.entries[0].operator == "alice"


def test_replay_missing_log_returns_error(tmp_path: Path) -> None:
    result = replay_audit_log(tmp_path / "missing.log")
    assert not result.success
    assert result.total == 0
    assert "not found" in result.errors[0]


def test_replay_entry_to_dict(log_file: Path) -> None:
    result = replay_audit_log(log_file, namespace="staging")
    d = result.entries[0].to_dict()
    assert d["namespace"] == "staging"
    assert d["operator"] == "bob"
    assert isinstance(d["changes"], list)


def test_summarise_replay_success(log_file: Path) -> None:
    result = replay_audit_log(log_file)
    msg = summarise_replay(result)
    assert "3" in msg


def test_summarise_replay_failure(tmp_path: Path) -> None:
    result = replay_audit_log(tmp_path / "nope.log")
    msg = summarise_replay(result)
    assert "failed" in msg.lower()
