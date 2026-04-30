"""Tests for vaultpatch.similarity_hook."""
from __future__ import annotations

import pytest

from vaultpatch.similarity import SimilarityConfig, SimilarityResult, SimilarityViolation
from vaultpatch.similarity_hook import (
    abort_on_similarity_failure,
    echo_similarity_results,
    run_similarity_check,
)


def _violation() -> SimilarityViolation:
    return SimilarityViolation(
        path_a="ns/a", key_a="pw", path_b="ns/b", key_b="pw", ratio=1.0
    )


def test_run_similarity_check_delegates():
    secrets = {
        "ns/a": {"pw": "same"},
        "ns/b": {"pw": "same"},
    }
    result = run_similarity_check(secrets, SimilarityConfig(threshold=0.85))
    assert result.has_violations


def test_run_similarity_check_clean():
    secrets = {
        "ns/a": {"pw": "aaaa"},
        "ns/b": {"pw": "zzzz"},
    }
    result = run_similarity_check(secrets, SimilarityConfig(threshold=0.85))
    assert not result.has_violations


def test_echo_similarity_results_ok(capsys):
    result = SimilarityResult(violations=[], checked=5)
    echo_similarity_results(result)
    out = capsys.readouterr().out
    assert "ok" in out
    assert "5" in out


def test_echo_similarity_results_violations(capsys):
    result = SimilarityResult(violations=[_violation()], checked=1)
    echo_similarity_results(result)
    err = capsys.readouterr().err
    assert "1 violation" in err
    assert "SIMILAR" in err


def test_abort_on_similarity_failure_no_violations_does_not_raise():
    result = SimilarityResult(violations=[], checked=0)
    abort_on_similarity_failure(result)  # should not raise


def test_abort_on_similarity_failure_raises_system_exit():
    result = SimilarityResult(violations=[_violation()], checked=1)
    with pytest.raises(SystemExit):
        abort_on_similarity_failure(result)
