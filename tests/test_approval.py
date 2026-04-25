"""Tests for vaultpatch.approval."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vaultpatch.approval import (
    ApprovalStore,
    ApprovalViolation,
    check_approvals,
    load_store,
    save_store,
)


@pytest.fixture()
def store() -> ApprovalStore:
    s = ApprovalStore()
    s.approve("secret/app/db", "alice", "JIRA-42")
    s.approve("secret/app/api", "bob")
    return s


def test_approve_creates_entry(store: ApprovalStore) -> None:
    entry = store.get("secret/app/db")
    assert entry is not None
    assert entry.approved_by == "alice"
    assert entry.comment == "JIRA-42"


def test_approve_overwrites_existing(store: ApprovalStore) -> None:
    store.approve("secret/app/db", "carol", "re-approved")
    entries = [e for e in store.all() if e.path == "secret/app/db"]
    assert len(entries) == 1
    assert entries[0].approved_by == "carol"


def test_revoke_removes_entry(store: ApprovalStore) -> None:
    removed = store.revoke("secret/app/api")
    assert removed is True
    assert store.get("secret/app/api") is None


def test_revoke_missing_returns_false(store: ApprovalStore) -> None:
    assert store.revoke("secret/nonexistent") is False


def test_check_approvals_no_violations(store: ApprovalStore) -> None:
    result = check_approvals(["secret/app/db", "secret/app/api"], store)
    assert not result.has_violations


def test_check_approvals_missing_path(store: ApprovalStore) -> None:
    result = check_approvals(["secret/app/db", "secret/missing"], store)
    assert result.has_violations
    assert len(result.violations) == 1
    assert result.violations[0].path == "secret/missing"


def test_violation_str() -> None:
    v = ApprovalViolation(path="secret/x")
    assert "secret/x" in str(v)


def test_save_and_load_roundtrip(tmp_path: Path, store: ApprovalStore) -> None:
    fpath = tmp_path / "approvals.json"
    save_store(store, fpath)
    loaded = load_store(fpath)
    paths = {e.path for e in loaded.all()}
    assert "secret/app/db" in paths
    assert "secret/app/api" in paths


def test_load_missing_file_returns_empty_store(tmp_path: Path) -> None:
    store = load_store(tmp_path / "nonexistent.json")
    assert store.all() == []


def test_to_dict_structure(store: ApprovalStore) -> None:
    d = store.to_dict()
    assert "approvals" in d
    assert isinstance(d["approvals"], list)
    assert all("path" in e and "approved_by" in e for e in d["approvals"])
