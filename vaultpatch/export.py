"""Export report results to JSON or CSV formats."""
from __future__ import annotations

import csv
import json
import io
from dataclasses import asdict
from typing import Literal

from vaultpatch.report import Report

ExportFormat = Literal["json", "csv"]


def export_report(report: Report, fmt: ExportFormat) -> str:
    """Serialize a Report to the requested format string."""
    if fmt == "json":
        return _to_json(report)
    if fmt == "csv":
        return _to_csv(report)
    raise ValueError(f"Unsupported export format: {fmt}")


def _to_json(report: Report) -> str:
    rows = []
    for entry in report.entries:
        for diff in entry.diffs:
            rows.append({
                "namespace": entry.namespace,
                "path": diff.path,
                "key": diff.key,
                "change_type": diff.label(),
                "old_value": diff.old_value,
                "new_value": diff.new_value,
            })
    return json.dumps(rows, indent=2)


def _to_csv(report: Report) -> str:
    fieldnames = ["namespace", "path", "key", "change_type", "old_value", "new_value"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for entry in report.entries:
        for diff in entry.diffs:
            writer.writerow({
                "namespace": entry.namespace,
                "path": diff.path,
                "key": diff.key,
                "change_type": diff.label(),
                "old_value": diff.old_value,
                "new_value": diff.new_value,
            })
    return buf.getvalue()
