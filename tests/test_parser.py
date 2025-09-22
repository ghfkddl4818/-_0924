from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.parser.extract import Parser


@pytest.mark.parametrize(
    "fixture_name,expected",
    [
        (
            "sample1.html",
            {
                "company": "Acme Corp",
                "services": [
                    "Robotics Integration",
                    "Predictive Maintenance",
                    "IoT Dashboards",
                ],
                "contact": {
                    "email": "hello@acme.example",
                    "phone": "+1 555 010 9999",
                },
                "summary": "Acme Corp builds automation solutions for manufacturers.",
                "missing": [],
            },
        ),
        (
            "sample2.html",
            {
                "company": "Skyline Consulting",
                "services": [
                    "Cloud Migration",
                    "DevOps Coaching",
                    "Automation Playbooks",
                ],
                "contact": {
                    "email": "contact@skyline.io",
                    "phone": "+44 20 7946 0958",
                },
                "summary": "Consulting for digital transformation.",
                "missing": [],
            },
        ),
    ],
)
def test_parser_end_to_end(fixture_name: str, expected: dict[str, object]) -> None:
    parser = Parser()
    html = (FIXTURE_DIR / fixture_name).read_text(encoding="utf-8")

    result = parser.parse(html)

    assert result["company"] == expected["company"]
    assert result["services"] == expected["services"]
    assert result["contact"] == expected["contact"]
    assert result["summary"] == expected["summary"]
    assert result["meta"]["missing"] == expected["missing"]
