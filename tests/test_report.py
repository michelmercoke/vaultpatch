import pytest
from vaultpatch.diff import SecretDiff
from vaultpatch.report import Report, ReportEntry, build_report
from unittest.mock import MagicMock


def _diff(key, old, new):
    return SecretDiff(key=key, old_value=old, new_value=new)


def test_report_empty():
    report = Report()
    assert not report.has_changes
    assert report.total_changes == 0
    assert report.render() == "No changes detected."


def test_report_add_entry():
    report = Report()
    report.add("ns1", "secret/app", [_diff("KEY", None, "val")])
    assert report.has_changes
    assert report.total_changes == 1


def test_report_add_empty_diffs_ignored():
    report = Report()
    report.add("ns1", "secret/app", [])
    assert not report.has_changes


def test_entry_summary_added():
    entry = ReportEntry("ns", "path", [_diff("K", None, "v")])
    assert "+1" in entry.summary


def test_entry_summary_removed():
    entry = ReportEntry("ns", "path", [_diff("K", "v", None)])
    assert "-1" in entry.summary


def test_entry_summary_changed():
    entry = ReportEntry("ns", "path", [_diff("K", "old", "new")])
    assert "~1" in entry.summary


def test_render_includes_namespace_and_path():
    report = Report()
    report.add("prod", "secret/db", [_diff("PASS", "old", "new")])
    output = report.render()
    assert "[prod]" in output
    assert "secret/db" in output
    assert "PASS" in output


def test_build_report_from_compare_result():
    compare_result = MagicMock()
    compare_result.by_namespace = {
        "staging": {
            "secret/svc": [_diff("TOKEN", None, "abc")]
        }
    }
    report = build_report(compare_result)
    assert report.has_changes
    assert report.entries[0].namespace == "staging"
    assert report.entries[0].path == "secret/svc"
