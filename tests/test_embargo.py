"""Tests for vaultpatch.embargo."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from vaultpatch.embargo import (
    EmbargoConfig,
    EmbargoWindow,
    check_embargo,
)


ACTIVE_START = "2099-01-01T00:00:00+00:00"
ACTIVE_END = "2099-12-31T23:59:59+00:00"
PAST_START = "2000-01-01T00:00:00+00:00"
PAST_END = "2000-12-31T23:59:59+00:00"

NOW = datetime(2099, 6, 15, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def active_window() -> EmbargoWindow:
    return EmbargoWindow(
        label="freeze",
        path_pattern="secret/prod/*",
        start=ACTIVE_START,
        end=ACTIVE_END,
    )


def test_active_embargo_produces_violation(active_window):
    config = EmbargoConfig(windows=[active_window])
    result = check_embargo(["secret/prod/db"], config, now=NOW)
    assert result.has_violations
    assert result.violations[0].path == "secret/prod/db"
    assert "freeze" in result.violations[0].reason


def test_expired_embargo_produces_no_violation():
    window = EmbargoWindow(
        label="old", path_pattern="secret/prod/*", start=PAST_START, end=PAST_END
    )
    config = EmbargoConfig(windows=[window])
    result = check_embargo(["secret/prod/db"], config, now=NOW)
    assert not result.has_violations


def test_non_matching_path_produces_no_violation(active_window):
    config = EmbargoConfig(windows=[active_window])
    result = check_embargo(["secret/staging/db"], config, now=NOW)
    assert not result.has_violations


def test_multiple_paths_only_matching_violated(active_window):
    config = EmbargoConfig(windows=[active_window])
    paths = ["secret/prod/api", "secret/dev/api"]
    result = check_embargo(paths, config, now=NOW)
    assert len(result.violations) == 1
    assert result.violations[0].path == "secret/prod/api"


def test_violation_str_contains_path_and_reason(active_window):
    config = EmbargoConfig(windows=[active_window])
    result = check_embargo(["secret/prod/x"], config, now=NOW)
    text = str(result.violations[0])
    assert "secret/prod/x" in text
    assert "embargo" in text


def test_from_dict_builds_config():
    data = {
        "windows": [
            {
                "label": "release-freeze",
                "path_pattern": "secret/prod/*",
                "start": ACTIVE_START,
                "end": ACTIVE_END,
            }
        ]
    }
    config = EmbargoConfig.from_dict(data)
    assert len(config.windows) == 1
    assert config.windows[0].label == "release-freeze"


def test_empty_config_produces_no_violations():
    config = EmbargoConfig(windows=[])
    result = check_embargo(["secret/prod/db"], config, now=NOW)
    assert not result.has_violations


def test_wildcard_pattern_matches_multiple_levels():
    window = EmbargoWindow(
        label="all", path_pattern="secret/*", start=ACTIVE_START, end=ACTIVE_END
    )
    config = EmbargoConfig(windows=[window])
    result = check_embargo(["secret/prod", "secret/staging"], config, now=NOW)
    assert len(result.violations) == 2
