"""Tests for vaultpatch.ttl — TTL detection logic."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from vaultpatch.ttl import TTLEntry, TTLReport, check_ttl


def _future(days: float) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=days)


def _past(days: float) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


# --- TTLEntry ---

def test_entry_is_expired_when_past():
    entry = TTLEntry(path="secret/db", namespace="prod", expires_at=_past(1))
    assert entry.is_expired is True


def test_entry_not_expired_when_future():
    entry = TTLEntry(path="secret/db", namespace="prod", expires_at=_future(10))
    assert entry.is_expired is False


def test_entry_is_warning_within_threshold():
    entry = TTLEntry(path="secret/db", namespace="prod", expires_at=_future(3), warn_days=7)
    assert entry.is_warning is True


def test_entry_not_warning_beyond_threshold():
    entry = TTLEntry(path="secret/db", namespace="prod", expires_at=_future(30), warn_days=7)
    assert entry.is_warning is False


def test_entry_expired_is_not_also_warning():
    entry = TTLEntry(path="secret/db", namespace="prod", expires_at=_past(1), warn_days=7)
    assert entry.is_expired is True
    assert entry.is_warning is False


def test_entry_to_dict_keys():
    entry = TTLEntry(path="secret/db", namespace="prod", expires_at=_future(5))
    d = entry.to_dict()
    assert set(d.keys()) == {"path", "namespace", "expires_at", "days_remaining", "is_expired", "is_warning"}


# --- check_ttl ---

def test_check_ttl_classifies_correctly():
    metadata = {
        "secret/expired": _past(2).isoformat(),
        "secret/warning": _future(3).isoformat(),
        "secret/healthy": _future(30).isoformat(),
    }
    report = check_ttl(metadata, namespace="staging", warn_days=7)
    assert len(report.expired) == 1
    assert len(report.warning) == 1
    assert len(report.healthy) == 1


def test_check_ttl_skips_invalid_dates():
    metadata = {"secret/bad": "not-a-date"}
    report = check_ttl(metadata, namespace="dev")
    assert report.entries == []


def test_check_ttl_empty_metadata():
    report = check_ttl({}, namespace="dev")
    assert report.entries == []
    assert report.expired == []
    assert report.warning == []
    assert report.healthy == []


def test_check_ttl_naive_datetime_treated_as_utc():
    naive = datetime.now() - timedelta(days=1)
    metadata = {"secret/x": naive.isoformat()}
    report = check_ttl(metadata, namespace="prod")
    assert len(report.expired) == 1
