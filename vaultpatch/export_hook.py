"""CLI integration helpers for the export feature."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from vaultpatch.export import ExportFormat, export_report
from vaultpatch.report import Report


def write_export(
    report: Report,
    fmt: ExportFormat,
    output: Optional[str] = None,
) -> None:
    """Render *report* in *fmt* and write to *output* path or stdout."""
    content = export_report(report, fmt)
    if output:
        dest = Path(output)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        _echo(f"Exported {fmt.upper()} report to {dest}")
    else:
        sys.stdout.write(content)


def _echo(msg: str) -> None:
    sys.stderr.write(msg + "\n")


def default_filename(fmt: ExportFormat) -> str:
    """Return a sensible default output filename for the given format."""
    return f"vaultpatch-report.{fmt}"
