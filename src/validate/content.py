"""Content quality validation utilities."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .schema import ValidationIssue

_PLACEHOLDER_TOKENS = {"tbd", "todo", "lorem ipsum"}


def _normalise_text(value: str | None) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def validate_content(data: Any) -> tuple[list[ValidationIssue], dict[str, int]]:
    """Perform content-focused validation on the payload."""
    issues: list[ValidationIssue] = []

    if not isinstance(data, Mapping):
        return issues, {"content_checked": 0}

    records = data.get("records")
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        return issues, {"content_checked": 0}

    checked = 0
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            continue
        checked += 1

        identifier = record.get("id", index)

        title = record.get("title")
        if not isinstance(title, str) or not title.strip():
            issues.append(
                ValidationIssue(
                    validator="content",
                    item=identifier,
                    field="title",
                    message="Title must be a non-empty string.",
                )
            )

        body = record.get("body")
        normalised_body = _normalise_text(body)
        if not normalised_body:
            issues.append(
                ValidationIssue(
                    validator="content",
                    item=identifier,
                    field="body",
                    message="Body must contain descriptive text.",
                )
            )
        elif len(normalised_body) < 40:
            issues.append(
                ValidationIssue(
                    validator="content",
                    item=identifier,
                    field="body",
                    message="Body content is too short (minimum 40 characters).",
                )
            )
        else:
            lowered = normalised_body.lower()
            if any(token in lowered for token in _PLACEHOLDER_TOKENS):
                issues.append(
                    ValidationIssue(
                        validator="content",
                        item=identifier,
                        field="body",
                        message="Body contains placeholder text that must be replaced.",
                    )
                )

    return issues, {"content_checked": checked}