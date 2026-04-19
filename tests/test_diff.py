"""Tests for vaultpatch.diff module."""
import pytest
from vaultpatch.diff import SecretDiff, diff_secrets, format_diff


CURRENT = {"db_pass": "old_pass", "api_key": "abc123", "stale_key": "to_remove"}
DESIRED = {"db_pass": "new_pass", "api_key": "abc123", "fresh_key": "brand_new"}


def test_diff_detects_changed():
    diffs = diff_secrets("secret/app", CURRENT, DESIRED)
    changed = [d for d in diffs if d.key == "db_pass"]
    assert len(changed) == 1
    assert changed[0].is_changed
    assert changed[0].label() == "changed"


def test_diff_detects_added():
    diffs = diff_secrets("secret/app", CURRENT, DESIRED)
    added = [d for d in diffs if d.key == "fresh_key"]
    assert len(added) == 1
    assert added[0].is_added
    assert added[0].old_value is None


def test_diff_detects_removed():
    diffs = diff_secrets("secret/app", CURRENT, DESIRED)
    removed = [d for d in diffs if d.key == "stale_key"]
    assert len(removed) == 1
    assert removed[0].is_removed
    assert removed[0].new_value is None


def test_diff_ignores_unchanged():
    diffs = diff_secrets("secret/app", CURRENT, DESIRED)
    keys = {d.key for d in diffs}
    assert "api_key" not in keys


def test_diff_empty_inputs():
    assert diff_secrets("secret/empty", {}, {}) == []


def test_format_diff_redacted():
    diffs = diff_secrets("secret/app", CURRENT, DESIRED)
    output = format_diff(diffs, redact=True)
    assert "<redacted>" in output
    assert "old_pass" not in output


def test_format_diff_plain():
    diffs = diff_secrets("secret/app", CURRENT, DESIRED)
    output = format_diff(diffs, redact=False)
    assert "old_pass" in output
    assert "new_pass" in output


def test_format_diff_no_diffs():
    assert format_diff([]) == "No differences found."


def test_diff_path_preserved():
    diffs = diff_secrets("secret/myapp/prod", {"x": "1"}, {"x": "2"})
    assert diffs[0].path == "secret/myapp/prod"
