"""Notification hooks for vaultpatch diff/apply results."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

import httpx

from vaultpatch.report import Report


@dataclass
class NotifyConfig:
    webhook_url: str
    on_diff: bool = True
    on_apply: bool = True
    mention: Optional[str] = None

    @classmethod
    def from_env(cls) -> Optional["NotifyConfig"]:
        url = os.environ.get("VAULTPATCH_WEBHOOK_URL")
        if not url:
            return None
        return cls(
            webhook_url=url,
            on_diff=os.environ.get("VAULTPATCH_NOTIFY_ON_DIFF", "true").lower() == "true",
            on_apply=os.environ.get("VAULTPATCH_NOTIFY_ON_APPLY", "true").lower() == "true",
            mention=os.environ.get("VAULTPATCH_NOTIFY_MENTION"),
        )


@dataclass
class NotifyResult:
    sent: bool
    status_code: Optional[int] = None
    error: Optional[str] = None


def _build_payload(report: Report, mode: str, mention: Optional[str]) -> dict:
    total = report.total_changes()
    lines = []
    if mention:
        lines.append(mention)
    lines.append(f"*vaultpatch {mode}* — {total} change(s) across {len(report.entries)} path(s)")
    for entry in report.entries:
        if entry.diffs:
            lines.append(f"  • `{entry.namespace}/{entry.path}`: {entry.summary()}")
    return {"text": "\n".join(lines)}


def send_notification(
    report: Report,
    mode: str,
    config: NotifyConfig,
    *,
    timeout: int = 5,
) -> NotifyResult:
    if not report.total_changes():
        return NotifyResult(sent=False)
    payload = _build_payload(report, mode, config.mention)
    try:
        resp = httpx.post(config.webhook_url, json=payload, timeout=timeout)
        return NotifyResult(sent=True, status_code=resp.status_code)
    except Exception as exc:  # noqa: BLE001
        return NotifyResult(sent=False, error=str(exc))
