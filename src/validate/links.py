"""Link validation helpers."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from .schema import ValidationIssue


def validate_links(
    data: Any,
    *,
    link_checker: Callable[[str], bool] | None = None,
) -> tuple[list[ValidationIssue], dict[str, int]]:
    """Validate link collections without performing network requests."""
    issues: list[ValidationIssue] = []

    if not isinstance(data, Mapping):
        return issues, {"links_checked": 0}

    records = data.get("records")
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        return issues, {"links_checked": 0}

    links_checked = 0
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            continue

        identifier = record.get("id", index)
        raw_links = record.get("links")

        if raw_links is None:
            continue

        if not isinstance(raw_links, Sequence) or isinstance(raw_links, (str, bytes)):
            issues.append(
                ValidationIssue(
                    validator="links",
                    item=identifier,
                    field="links",
                    message="Links must be provided as a sequence of URLs.",
                )
            )
            continue

        seen: set[str] = set()
        for link in raw_links:
            if not isinstance(link, str):
                issues.append(
                    ValidationIssue(
                        validator="links",
                        item=identifier,
                        field="links",
                        message="Link entries must be strings.",
                    )
                )
                continue

            candidate = link.strip()
            if not candidate:
                issues.append(
                    ValidationIssue(
                        validator="links",
                        item=identifier,
                        field="links",
                        message="Link entries must not be empty.",
                    )
                )
                continue

            if not candidate.lower().startswith(("http://", "https://")):
                issues.append(
                    ValidationIssue(
                        validator="links",
                        item=identifier,
                        field="links",
                        message=f"Unsupported link scheme in '{candidate}'.",
                    )
                )
                continue

            if candidate in seen:
                issues.append(
                    ValidationIssue(
                        validator="links",
                        item=identifier,
                        field="links",
                        message=f"Duplicate link '{candidate}'.",
                    )
                )
                continue

            seen.add(candidate)

            if link_checker is not None:
                try:
                    reachable = link_checker(candidate)
                except Exception as exc:  # pragma: no cover - defensive branch
                    issues.append(
                        ValidationIssue(
                            validator="links",
                            item=identifier,
                            field="links",
                            message=f"Link checker raised {exc!r} for '{candidate}'.",
                        )
                    )
                    continue

                if not reachable:
                    issues.append(
                        ValidationIssue(
                            validator="links",
                            item=identifier,
                            field="links",
                            message=f"Unreachable link '{candidate}'.",
                        )
                    )
            links_checked += 1

    return issues, {"links_checked": links_checked}