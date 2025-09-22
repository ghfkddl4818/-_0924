"""Schema validation helpers and aggregate reporting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from collections.abc import Mapping, Sequence


@dataclass(slots=True)
class ValidationIssue:
    """Represents a single validation finding."""

    validator: str
    item: str | int | None
    field: str | None
    message: str

    def as_dict(self) -> dict[str, Any]:
        """Return a serialisable representation of the issue."""
        return {
            "validator": self.validator,
            "item": self.item,
            "field": self.field,
            "message": self.message,
        }


@dataclass(slots=True)
class Report:
    """Summary of validation results."""

    ok: bool
    issues: list[ValidationIssue]
    counts: dict[str, int]

    def as_dict(self) -> dict[str, Any]:
        """Return a serialisable representation of the report."""
        return {
            "ok": self.ok,
            "issues": [issue.as_dict() for issue in self.issues],
            "counts": dict(self.counts),
        }


def validate_schema(data: Any) -> tuple[list[ValidationIssue], dict[str, int]]:
    """Validate the structural schema of the provided data payload."""
    issues: list[ValidationIssue] = []
    if not isinstance(data, Mapping):
        issues.append(
            ValidationIssue(
                validator="schema",
                item=None,
                field=None,
                message="Top-level data must be a mapping that contains a 'records' key.",
            )
        )
        return issues, {"records": 0}

    records = data.get("records")
    if records is None:
        issues.append(
            ValidationIssue(
                validator="schema",
                item=None,
                field="records",
                message="Missing required 'records' collection.",
            )
        )
        return issues, {"records": 0}

    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        issues.append(
            ValidationIssue(
                validator="schema",
                item=None,
                field="records",
                message="'records' must be a sequence of mapping objects.",
            )
        )
        return issues, {"records": 0}

    record_count = len(records)
    for index, record in enumerate(records):
        identifier: str | int | None = index
        if isinstance(record, Mapping) and "id" in record:
            raw_id = record.get("id")
            if isinstance(raw_id, (str, int)):
                identifier = raw_id

        if not isinstance(record, Mapping):
            issues.append(
                ValidationIssue(
                    validator="schema",
                    item=identifier,
                    field=None,
                    message=f"Record #{index} must be a mapping of field values.",
                )
            )
            continue

        required_fields = ("id", "title", "body", "links")
        for field in required_fields:
            if field not in record:
                issues.append(
                    ValidationIssue(
                        validator="schema",
                        item=identifier,
                        field=field,
                        message=f"Missing required field '{field}'.",
                    )
                )

        record_id = record.get("id")
        if record_id is not None and not isinstance(record_id, (str, int)):
            issues.append(
                ValidationIssue(
                    validator="schema",
                    item=identifier,
                    field="id",
                    message="Field 'id' must be a string or integer.",
                )
            )

        title = record.get("title")
        if title is not None and not isinstance(title, str):
            issues.append(
                ValidationIssue(
                    validator="schema",
                    item=identifier,
                    field="title",
                    message="Field 'title' must be a string.",
                )
            )

        body = record.get("body")
        if body is not None and not isinstance(body, str):
            issues.append(
                ValidationIssue(
                    validator="schema",
                    item=identifier,
                    field="body",
                    message="Field 'body' must be a string.",
                )
            )

        links = record.get("links")
        if links is None:
            continue
        if not isinstance(links, Sequence) or isinstance(links, (str, bytes)):
            issues.append(
                ValidationIssue(
                    validator="schema",
                    item=identifier,
                    field="links",
                    message="Field 'links' must be a sequence of link strings.",
                )
            )
            continue

        for link in links:
            if not isinstance(link, str):
                issues.append(
                    ValidationIssue(
                        validator="schema",
                        item=identifier,
                        field="links",
                        message="Link entries must be strings.",
                    )
                )
                break

    return issues, {"records": record_count}


def _merge_counts(target: dict[str, int], incoming: Mapping[str, int]) -> None:
    for key, value in incoming.items():
        if key == "records" and key in target:
            target[key] = max(target[key], value)
        else:
            target[key] = target.get(key, 0) + value


def validate_all(
    data: Any,
    *,
    link_checker: Callable[[str], bool] | None = None,
) -> Report:
    """Run all validators and return a consolidated report."""
    from .content import validate_content
    from .links import validate_links

    issues: list[ValidationIssue] = []
    counts: dict[str, int] = {}
    validators_run = 0

    schema_issues, schema_counts = validate_schema(data)
    issues.extend(schema_issues)
    _merge_counts(counts, schema_counts)
    validators_run += 1

    content_issues, content_counts = validate_content(data)
    issues.extend(content_issues)
    _merge_counts(counts, content_counts)
    validators_run += 1

    link_issues, link_counts = validate_links(data, link_checker=link_checker)
    issues.extend(link_issues)
    _merge_counts(counts, link_counts)
    validators_run += 1

    counts["issues"] = len(issues)
    counts["validators"] = validators_run

    counts.setdefault("records", schema_counts.get("records", 0))
    counts.setdefault("content_checked", content_counts.get("content_checked", 0))
    counts.setdefault("links_checked", link_counts.get("links_checked", 0))

    return Report(ok=not issues, issues=issues, counts=counts)