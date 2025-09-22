from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from normalize.company import canonical_company_name, normalize_company_name
from normalize.contact import contact_dedup_key, normalize_email, normalize_phone


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("  ACME   INC.  ", "Acme INC."),
        ("\u200bacme llc\u200b", "Acme LLC"),
        ("café\t société", "Café Société"),
        ("Data—Works GmbH", "Data-Works GmbH"),
    ],
)
def test_normalize_company_name(raw: str, expected: str) -> None:
    assert normalize_company_name(raw) == expected


def test_canonical_company_name_variants() -> None:
    variants = [
        "The Acme, Inc.",
        "ACME INC",
        "Acme Incorporated",
        "acme ltd",
    ]
    keys = {canonical_company_name(value) for value in variants}
    assert keys == {"acme"}


def test_canonical_company_handles_accents_and_suffix() -> None:
    assert canonical_company_name("Café Société, S.A.") == "cafe societe"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("  MAILTO:Info@Example.COM ", "info@example.com"),
        ("<sales+eu@Example.com>", "sales+eu@example.com"),
    ],
)
def test_normalize_email(raw: str, expected: str) -> None:
    assert normalize_email(raw) == expected


def test_normalize_email_invalid() -> None:
    assert normalize_email("not-an-email") is None


@pytest.mark.parametrize(
    "raw,expected",
    [
        (" (555) 010-9999 ext. 42 ", "5550109999"),
        ("+1 (555) 010-9999", "+15550109999"),
        ("00 44 20 7946 0958", "+442079460958"),
    ],
)
def test_normalize_phone(raw: str, expected: str) -> None:
    assert normalize_phone(raw) == expected


def test_normalize_phone_invalid() -> None:
    assert normalize_phone("call us maybe") is None


def test_contact_dedup_key_prioritizes_email() -> None:
    assert contact_dedup_key("Info@Example.com", "+1 555 010-9999") == "email:info@example.com"
    assert contact_dedup_key(None, "(555) 010-9999") == "phone:5550109999"
    assert contact_dedup_key("bad", "  ") is None