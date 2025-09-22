"""Company name normalization utilities."""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

__all__ = ["normalize_company_name", "canonical_company_name", "BUSINESS_SUFFIXES"]

_ZERO_WIDTH_PATTERN = re.compile(r"[\u200B-\u200D\uFEFF]")
_HYPHEN_PATTERN = re.compile(r"[‐‑‒–—―]")
_WHITESPACE_PATTERN = re.compile(r"\s+")
_WORD_PATTERN = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)?", re.UNICODE)

BUSINESS_SUFFIXES = frozenset(
    {
        "ag",
        "bv",
        "co",
        "company",
        "corporation",
        "corp",
        "gmbh",
        "inc",
        "incorporated",
        "kg",
        "kk",
        "llc",
        "ltd",
        "limited",
        "nv",
        "oy",
        "oyj",
        "plc",
        "pty",
        "pte",
        "sa",
        "sas",
        "sasu",
        "sarl",
        "sro",
        "srl",
        "ug",
    }
)

_ARTICLE_PREFIXES = {"the", "a", "an"}


def normalize_company_name(name: Optional[str]) -> Optional[str]:
    """Return a display-friendly company name with consistent spacing/casing."""
    if name is None:
        return None
    text = unicodedata.normalize("NFKC", name)
    text = _ZERO_WIDTH_PATTERN.sub("", text)
    text = text.replace("\u00A0", " ")
    text = _HYPHEN_PATTERN.sub("-", text)
    text = text.strip()
    if not text:
        return None
    text = _WHITESPACE_PATTERN.sub(" ", text)
    text = _normalize_case(text)
    return text


def canonical_company_name(name: Optional[str]) -> Optional[str]:
    """Return a canonical identifier suitable for deduplication."""
    normalized = normalize_company_name(name)
    if not normalized:
        return None
    ascii_name = unicodedata.normalize("NFKD", normalized)
    ascii_name = "".join(ch for ch in ascii_name if not unicodedata.combining(ch))
    ascii_name = ascii_name.replace("&", " and ").replace("@", " at ")
    ascii_name = re.sub(r"[^a-z0-9]+", " ", ascii_name.lower())
    tokens = ascii_name.split()
    while tokens and tokens[0] in _ARTICLE_PREFIXES:
        tokens.pop(0)
    tokens = _trim_business_suffix(tokens)
    if not tokens:
        return None
    return " ".join(tokens)


def _normalize_case(text: str) -> str:
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return text
    if all(ch.isupper() for ch in letters):
        return _titlecase_preserving_initialisms(text.lower())
    if all(ch.islower() for ch in letters):
        return _titlecase_preserving_initialisms(text)
    return text


def _titlecase_preserving_initialisms(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        word = match.group(0)
        if len(word) <= 3:
            return word.upper()
        return word[0].upper() + word[1:].lower()

    base = text.lower()
    return _WORD_PATTERN.sub(repl, base)


def _trim_business_suffix(tokens: list[str]) -> list[str]:
    working = list(tokens)
    max_width = 4
    while working:
        removed = False
        limit = min(max_width, len(working))
        for width in range(limit, 0, -1):
            chunk = "".join(working[-width:])
            if chunk in BUSINESS_SUFFIXES:
                del working[-width:]
                removed = True
                break
        if not removed:
            break
    return working
