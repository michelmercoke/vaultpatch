"""Retry logic for Vault API calls."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, TypeVar, Optional

T = TypeVar("T")

DEFAULT_ATTEMPTS = 3
DEFAULT_DELAY = 1.0
DEFAULT_BACKOFF = 2.0


@dataclass
class RetryConfig:
    attempts: int = DEFAULT_ATTEMPTS
    delay: float = DEFAULT_DELAY
    backoff: float = DEFAULT_BACKOFF
    retryable_exceptions: tuple = field(
        default_factory=lambda: (ConnectionError, TimeoutError)
    )


@dataclass
class RetryResult:
    success: bool
    value: object = None
    error: Optional[str] = None
    attempts_made: int = 0


def with_retry(
    fn: Callable[[], T],
    config: Optional[RetryConfig] = None,
    *,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> RetryResult:
    """Call *fn* up to config.attempts times, backing off on retryable errors.

    Args:
        fn: The callable to invoke. It must take no arguments; use
            ``functools.partial`` to bind arguments beforehand.
        config: Retry configuration. Defaults to :class:`RetryConfig` with
            ``attempts=3``, ``delay=1.0`` s, and ``backoff=2.0``.
        sleep_fn: Callable used to sleep between attempts. Defaults to
            ``time.sleep``; pass a no-op or mock in tests.

    Returns:
        A :class:`RetryResult` describing whether the call ultimately
        succeeded, the return value (if any), the last error message, and
        the total number of attempts made.
    """
    cfg = config or RetryConfig()
    delay = cfg.delay
    last_error: Optional[Exception] = None

    for attempt in range(1, cfg.attempts + 1):
        try:
            result = fn()
            return RetryResult(success=True, value=result, attempts_made=attempt)
        except cfg.retryable_exceptions as exc:  # type: ignore[misc]
            last_error = exc
            if attempt < cfg.attempts:
                sleep_fn(delay)
                delay *= cfg.backoff
        except Exception as exc:
            return RetryResult(
                success=False,
                error=str(exc),
                attempts_made=attempt,
            )

    return RetryResult(
        success=False,
        error=str(last_error),
        attempts_made=cfg.attempts,
    )
