"""Tests for vaultpatch.export."""
import json
import csv
import io
import pytest

from vaultpatch.diff import SecretDiff
from vaultpatch.report import Report, ReportEntry
from vaultpatch.export import export_report


@pytest.fixture()
def sample_report():
    d1 = SecretDiff(path="secret/a", key="password", old_value="old", new_value="new")
    d2 = SecretDiff(path="secret/a", key="token", old_value=None, new_value="abc")
    entry = ReportEntry(namespace="ns1", diffs=[d1, d2])
    r = Report()
    r.add(entry)
    return r


def test_export_json_structure(sample_report):
    out = export_report(sample_report, "json")
    rows = json.loads(out)
    assert len(rows) == 2
    assert rows[0]["namespace"] == "ns1"
    assert rows[0]["path"] == "secret/a"
    assert rows[0]["key"] == "password"
    assert rows[0]["change_type"] == "changed"


def test_export_json_added(sample_report):
    out = export_report(sample_report, "json")
    rows = json.loads(out)
    added = [r for r in rows if r["key"] == "token"]
    assert added[0]["change_type"] == "added"
    assert added[0]["old_value"] is None


def test_export_csv_headers(sample_report):
    out = export_report(sample_report, "csv")
    reader = csv.DictReader(io.StringIO(out))
    assert set(reader.fieldnames) == {"namespace", "path", "key", "change_type", "old_value", "new_value"}


def test_export_csv_rows(sample_report):
    out = export_report(sample_report, "csv")
    reader = csv.DictReader(io.StringIO(out))
    rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["namespace"] == "ns1"


def test_export_empty_report():
    r = Report()
    assert json.loads(export_report(r, "json")) == []
    out = export_report(r, "csv")
    reader = csv.DictReader(io.StringIO(out))
    assert list(reader) == []


def test_export_invalid_format(sample_report):
    with pytest.raises(ValueError, match="Unsupported"):
        export_report(sample_report, "xml")  # type: ignore
