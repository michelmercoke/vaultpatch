"""Schema validation for secret values against user-defined rules."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SchemaRule:
    key_pattern: str
    required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    regex: Optional[str] = None

    def matches_key(self, key: str) -> bool:
        return bool(re.fullmatch(self.key_pattern.replace("*", ".*"), key))

    def validate_value(self, key: str, value: str) -> List[str]:
        errors: List[str] = []
        if self.min_length is not None and len(value) < self.min_length:
            errors.append(
                f"{key}: value too short (min {self.min_length}, got {len(value)})"
            )
        if self.max_length is not None and len(value) > self.max_length:
            errors.append(
                f"{key}: value too long (max {self.max_length}, got {len(value)})"
            )
        if self.regex is not None and not re.fullmatch(self.regex, value):
            errors.append(f"{key}: value does not match pattern '{self.regex}'")
        return errors


@dataclass
class SchemaConfig:
    rules: List[SchemaRule] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict) -> "SchemaConfig":
        rules = [
            SchemaRule(
                key_pattern=r["key_pattern"],
                required=r.get("required", False),
                min_length=r.get("min_length"),
                max_length=r.get("max_length"),
                regex=r.get("regex"),
            )
            for r in data.get("rules", [])
        ]
        return cls(rules=rules)


@dataclass
class SchemaCheckResult:
    errors: List[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0


def check_secrets(secrets: Dict[str, str], schema: SchemaConfig) -> SchemaCheckResult:
    """Validate a flat secrets dict against a SchemaConfig."""
    result = SchemaCheckResult()
    for rule in schema.rules:
        matched_keys = [k for k in secrets if rule.matches_key(k)]
        if rule.required and not matched_keys:
            result.errors.append(f"required key matching '{rule.key_pattern}' is missing")
        for key in matched_keys:
            result.errors.extend(rule.validate_value(key, secrets[key]))
    return result
