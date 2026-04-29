"""Hook: build, persist, and compare fingerprints during a diff/apply run."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List

import click

from vaultpatch.fingerprint import (
    FingerprintEntry,
    FingerprintResult,
    build_fingerprint,
    compare_fingerprints,
)
from vaultpatch.fingerprint_store import (
    fingerprint_store_key,
    load_fingerprints,
    save_fingerprints,
)


def build_entries(
    namespace: str,
    secrets_by_path: Dict[str, Dict[str, str]],
) -> List[FingerprintEntry]:
    return [
        build_fingerprint(path, namespace, secrets)
        for path, secrets in secrets_by_path.items()
    ]


def check_and_update(
    namespace: str,
    secrets_by_path: Dict[str, Dict[str, str]],
    store_dir: Path,
) -> FingerprintResult:
    current = build_entries(namespace, secrets_by_path)
    store_file = store_dir / fingerprint_store_key(namespace)
    try:
        stored = load_fingerprints(store_file)
    except FileNotFoundError:
        stored = []
    result = compare_fingerprints(stored, current)
    save_fingerprints(store_file, current)
    return result


def echo_fingerprint_results(result: FingerprintResult) -> None:
    if not result.has_mismatches:
        click.echo("[fingerprint] all digests match")
        return
    for m in result.mismatches:
        click.echo(f"[fingerprint] MISMATCH: {m}", err=True)


def abort_on_fingerprint_mismatch(result: FingerprintResult) -> None:
    if result.has_mismatches:
        click.echo(
            f"[fingerprint] {len(result.mismatches)} digest mismatch(es) — aborting.",
            err=True,
        )
        sys.exit(1)
