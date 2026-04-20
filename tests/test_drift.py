"""Tests for vaultpatch.drift."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from vaultpatch.config import NamespaceConfig
from vaultpatch.diff import SecretDiff
from vaultpatch.drift import detect_drift, summarise_drift, DriftResult
from vaultpatch.fetch import FetchResult
from vaultpatch.snapshot import save_snapshot, snapshot_key


@pytest.fixture()
def ns_cfg():
    return NamespaceConfig(name="prod", address="http://vault:8200", token="tok", mount="secret", paths=["/app/db"])


@pytest.fixture()
def snap_dir(tmp_path):
    return str(tmp_path)


def _fetch(secrets: dict, error=None) -> FetchResult:
    return FetchResult(secrets=secrets, error=error)


def test_detect_drift_no_drift(ns_cfg, snap_dir):
    secrets = {"/app/db": {"user": "admin", "pass": "s3cr3t"}}
    save_snapshot(snap_dir, snapshot_key("prod"), secrets)
    result = detect_drift(_fetch(secrets), snap_dir, "prod")
    assert len(result) == 1
    assert not result[0].has_drift
    assert result[0].success


def test_detect_drift_changed_value(ns_cfg, snap_dir):
    old = {"/app/db": {"user": "admin", "pass": "old"}}
    new = {"/app/db": {"user": "admin", "pass": "new"}}
    save_snapshot(snap_dir, snapshot_key("prod"), old)
    result = detect_drift(_fetch(new), snap_dir, "prod")
    assert result[0].has_drift
    assert any(d.key == "pass" for d in result[0].diffs)


def test_detect_drift_added_key(ns_cfg, snap_dir):
    old = {"/app/db": {"user": "admin"}}
    new = {"/app/db": {"user": "admin", "pass": "new"}}
    save_snapshot(snap_dir, snapshot_key("prod"), old)
    result = detect_drift(_fetch(new), snap_dir, "prod")
    assert result[0].has_drift


def test_detect_drift_missing_snapshot(ns_cfg, snap_dir):
    secrets = {"/app/db": {"user": "admin"}}
    result = detect_drift(_fetch(secrets), snap_dir, "prod")
    assert len(result) == 1
    assert not result[0].success
    assert "snapshot" in result[0].path


def test_detect_drift_fetch_error(ns_cfg, snap_dir):
    fetch = _fetch({}, error="connection refused")
    result = detect_drift(fetch, snap_dir, "prod")
    assert len(result) == 1
    assert not result[0].success
    assert result[0].error == "connection refused"


def test_summarise_drift_all_clean():
    results = [
        DriftResult(namespace="prod", path="/a"),
        DriftResult(namespace="prod", path="/b"),
    ]
    summary = summarise_drift(results)
    assert "0 path(s) drifted" in summary
    assert "2 clean" in summary


def test_summarise_drift_mixed():
    diff = SecretDiff(key="x", old="1", new="2")
    results = [
        DriftResult(namespace="prod", path="/a", diffs=[diff]),
        DriftResult(namespace="prod", path="/b"),
        DriftResult(namespace="prod", path="/c", error="oops"),
    ]
    summary = summarise_drift(results)
    assert "1 path(s) drifted" in summary
    assert "1 clean" in summary
    assert "1 error(s)" in summary
