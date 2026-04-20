"""Template rendering for secret values using environment variable substitution."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_PLACEHOLDER_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::([^}]*))?\}")


@dataclass
class TemplateError:
    key: str
    placeholder: str
    message: str

    def __str__(self) -> str:
        return f"[{self.key}] '{self.placeholder}': {self.message}"


@dataclass
class TemplateResult:
    rendered: Dict[str, str] = field(default_factory=dict)
    errors: List[TemplateError] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


def _render_value(key: str, value: str, env: Dict[str, str]) -> tuple[str, List[TemplateError]]:
    """Expand ${VAR} and ${VAR:default} placeholders in *value*."""
    errors: List[TemplateError] = []

    def replacer(m: re.Match) -> str:
        var_name = m.group(1)
        default: Optional[str] = m.group(2)  # None when no default given
        resolved = env.get(var_name, default)
        if resolved is None:
            errors.append(
                TemplateError(
                    key=key,
                    placeholder=m.group(0),
                    message=f"environment variable '{var_name}' is not set and has no default",
                )
            )
            return m.group(0)  # leave placeholder unchanged on error
        return resolved

    rendered = _PLACEHOLDER_RE.sub(replacer, value)
    return rendered, errors


def render_secrets(
    secrets: Dict[str, str],
    env: Optional[Dict[str, str]] = None,
) -> TemplateResult:
    """Render all secret values, substituting environment-variable placeholders.

    Args:
        secrets: Mapping of secret key -> raw value (may contain placeholders).
        env:     Environment to resolve variables from; defaults to ``os.environ``.

    Returns:
        A :class:`TemplateResult` with the rendered mapping and any errors.
    """
    if env is None:
        env = dict(os.environ)

    result = TemplateResult()
    for key, value in secrets.items():
        rendered, errors = _render_value(key, value, env)
        result.rendered[key] = rendered
        result.errors.extend(errors)
    return result
