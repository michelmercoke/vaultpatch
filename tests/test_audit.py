"""Tests for vaultpatch.audit."""
import json
import pytest
from pathlib import Path

from vaultpatch.audit import (
    AuditEntry,
    build_entry,
    write_audit_log,
    load_audit_log,
)
from vaultpatch.diff import SecretDiff


@pytest.fixture
def tmp_log(tmp_path):
    return str(tmp_path / "audit" / "vaultpatch.log")


def _diff(key, old, new):
    return SecretDiff(key=key, old_value=old, new_value=new)


def test_build_entry_captures_changes():
    diffs = [_diff("DB_PASS", "old", "new"), _diff("API_KEY", None, "v1")]
    entry = build_entry("ns1", "secret/app", "apply", diffs)
    assert entry.namespace == "ns1"
    assert entry.path == "secret/app"
    assert entry.operation == "apply"
    assert len(entry.changes) == 2
    assert entry.error is None


def test_build_entry_excludes_unchanged():
    diffs = [_diff("UNCHANGED", "same", "same")]
    entry = build_entry("ns1", "secret/app", "diff", diffs)
    assert entry.changes == []


def test_build_entry_records_error():
    entry = build_entry("ns1", "secret/app", "diff", [], error="permission denied")
    assert entry.error == "permission denied"


def test_write_and_load_roundtrip(tmp_log):
    entries = [
        build_entry("ns1", "secret/a", "diff", [_diff("K", None, "v")]),
        build_entry("ns2", "secret/b", "apply", []),
    ]
    write_audit_log(entries, tmp_log)
    loaded = load_audit_log(tmp_log)
    assert len(loaded) == 2
    assert loaded[0].namespace == "ns1"
    assert loaded[1].namespace == "ns2"


def test_write_appends(tmp_log):
    e1 = build_entry("ns1", "secret/a", "diff", [])
    e2 = build_entry("ns2", "secret/b", "apply", [])
    write_audit_log([e1], tmp_log)
    write_audit_log([e2], tmp_log)
    loaded = load_audit_log(tmp_log)
    assert len(loaded) == 2


def test_load_missing_file_returns_empty(tmp_log):
    result = load_audit_log(tmp_log)
    assert result == []


def test_to_dict_is_json_serialisable():
    entry = build_entry("ns", "p", "diff", [])
    data = entry.to_dict()
    assert json.dumps(data)  # no exception
    assert data["operation"] == "diff"
