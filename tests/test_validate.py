from __future__ import annotations

from unittest.mock import Mock

from src.validate.schema import Report, ValidationIssue, validate_all


def test_validate_all_with_valid_payload() -> None:
    data = {
        "records": [
            {
                "id": "alpha",
                "title": "Alpha launch announcement",
                "body": "This announcement contains detailed information about the upcoming launch window.",
                "links": [
                    "https://example.com/details",
                    "https://example.com/faq",
                ],
            }
        ]
    }

    checker = Mock(side_effect=lambda url: True)

    report = validate_all(data, link_checker=checker)

    assert isinstance(report, Report)
    assert report.ok is True
    assert report.issues == []
    assert report.counts["records"] == 1
    assert report.counts["links_checked"] == 2
    assert report.counts["validators"] == 3
    assert report.counts["issues"] == 0
    assert checker.call_count == 2


def test_validate_all_reports_mixed_issues() -> None:
    data = {
        "records": [
            {
                "id": "beta",
                "title": " ",
                "body": "TODO finalize content",
                "links": [
                    "https://invalid.example.com/path",
                    "ftp://unsupported.example.com/resource",
                    "https://invalid.example.com/path",
                ],
            },
            "not-a-mapping",
        ]
    }

    checker = Mock(side_effect=lambda url: False)

    report = validate_all(data, link_checker=checker)

    assert report.ok is False
    assert report.counts["validators"] == 3
    assert report.counts["content_checked"] == 1
    assert report.counts["links_checked"] == 1
    assert report.counts["issues"] == len(report.issues)

    assert any(issue.validator == "schema" and "must be a mapping" in issue.message for issue in report.issues)
    assert any(issue.validator == "content" and "Title must be a non-empty string" in issue.message for issue in report.issues)
    assert any(issue.validator == "content" and "Body content is too short" in issue.message for issue in report.issues)
    assert any(issue.validator == "links" and "Unsupported link scheme" in issue.message for issue in report.issues)
    assert any(issue.validator == "links" and "Unreachable link" in issue.message for issue in report.issues)
    assert any(issue.validator == "links" and "Duplicate link" in issue.message for issue in report.issues)
    assert checker.call_count == 1