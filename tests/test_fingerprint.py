"""Tests for vaultpatch.fingerprint."""
import pytest

from vaultpatch.fingerprint import (
    FingerprintEntry,
    FingerprintMismatch,
    build_fingerprint,
    compare_fingerprints,
    _compute_digest,
)


def test_compute_digest_is_deterministic():
    secrets = {"key": "value", "other": "data"}
    assert _compute_digest(secrets) == _compute_digest(secrets)


def test_compute_digest_order_independent():
    a = {"x": "1", "y": "2"}
    b = {"y": "2", "x": "1"}
    assert _compute_digest(a) == _compute_digest(b)


def test_compute_digest_differs_on_value_change():
    a = {"key": "old"}
    b = {"key": "new"}
    assert _compute_digest(a) != _compute_digest(b)


def test_build_fingerprint_captures_keys():
    entry = build_fingerprint("secret/app", "dev", {"DB_PASS": "s3cr3t"})
    assert entry.path == "secret/app"
    assert entry.namespace == "dev"
    assert "DB_PASS" in entry.keys
    assert len(entry.digest) == 64  # sha256 hex


def test_build_fingerprint_to_dict():
    entry = build_fingerprint("secret/app", "dev", {"b": "2", "a": "1"})
    d = entry.to_dict()
    assert d["keys"] == ["a", "b"]  # sorted
    assert d["namespace"] == "dev"


def test_compare_no_mismatches_when_digests_match():
    entry = build_fingerprint("secret/app", "dev", {"k": "v"})
    result = compare_fingerprints([entry], [entry])
    assert not result.has_mismatches


def test_compare_detects_mismatch():
    stored = build_fingerprint("secret/app", "dev", {"k": "old"})
    current = build_fingerprint("secret/app", "dev", {"k": "new"})
    result = compare_fingerprints([stored], [current])
    assert result.has_mismatches
    assert len(result.mismatches) == 1
    m = result.mismatches[0]
    assert m.path == "secret/app"
    assert m.namespace == "dev"


def test_compare_no_stored_produces_no_mismatch():
    current = build_fingerprint("secret/app", "dev", {"k": "v"})
    result = compare_fingerprints([], [current])
    assert not result.has_mismatches


def test_mismatch_str_contains_path():
    m = FingerprintMismatch(
        path="secret/app",
        namespace="dev",
        stored="aabbccdd" + "0" * 56,
        current="11223344" + "0" * 56,
    )
    s = str(m)
    assert "secret/app" in s
    assert "aabbccdd" in s
    assert "11223344" in s


def test_compare_result_entries_are_current():
    stored = build_fingerprint("secret/app", "dev", {"k": "old"})
    current = build_fingerprint("secret/app", "dev", {"k": "new"})
    result = compare_fingerprints([stored], [current])
    assert result.entries[0].digest == current.digest
