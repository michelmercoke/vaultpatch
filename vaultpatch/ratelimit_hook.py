"""CLI hook for rate limit checks in vaultpatch."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

import click

from vaultpatch.ratelimit import (
    RateLimitConfig,
    RateLimitResult,
    RateLimitStore,
    check_rate_limit,
)

_DEFAULT_STORE = Path(".vaultpatch") / "ratelimit.json"


def load_store(path: Optional[Path] = None) -> RateLimitStore:
    return RateLimitStore.load(path or _DEFAULT_STORE)


def save_store(store: RateLimitStore) -> None:
    store.save()


def run_rate_limit_check(
    namespace: str,
    cfg: RateLimitConfig,
    store: RateLimitStore,
) -> RateLimitResult:
    store.prune(namespace)
    return check_rate_limit(namespace, cfg, store)


def echo_rate_limit_results(results: List[RateLimitResult]) -> None:
    for result in results:
        if result.has_violations:
            for v in result.violations:
                click.echo(f"  [rate-limit] {v}", err=True)
        else:
            click.echo(f"  [rate-limit] {result.namespace}: OK")


def abort_on_rate_limit_exceeded(results: List[RateLimitResult]) -> None:
    violated = [r for r in results if r.has_violations]
    if violated:
        click.echo(
            f"Aborting: rate limit exceeded for {len(violated)} namespace(s).",
            err=True,
        )
        sys.exit(1)


def record_writes(namespace: str, count: int, store: RateLimitStore) -> None:
    for _ in range(count):
        store.record(namespace)
