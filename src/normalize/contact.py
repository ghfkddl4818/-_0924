"""Contact detail normalization utilities."""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

__all__ = ["normalize_email", "normalize_phone", "contact_dedup_key"]

_EMAIL_PATTERN = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)
_EXTENSION_PATTERN = re.compile(r"(?:ext|x|extension)[\s.:]*\d+", re.IGNORECASE)


def normalize_email(value: Optional[str]) -> Optional[str]:
    """Normalize an email address and return a lower-cased canonical form."""
    if value is None:
        return None
    text = unicodedata.normalize("NFKC", value)
    text = text.strip()
    if not text:
        return None
    if text.lower().startswith("mailto:"):
        text = text.split(":", 1)[1]
    text = text.strip()
    if text.startswith("<") and text.endswith(">"):
        text = text[1:-1]
    text = text.replace(" ", "")
    text = text.rstrip(".,;:")
    text = text.lower()
    if not _EMAIL_PATTERN.fullmatch(text):
        return None
    return text


def normalize_phone(value: Optional[str]) -> Optional[str]:
    """Normalize a phone number returning digits with an optional leading '+'."""
    if value is None:
        return None
    text = unicodedata.normalize("NFKC", value)
    text = text.strip()
    if not text:
        return None
    text = text.replace("\u00A0", " ")
    text = text.replace("tel:", "")
    text = text.replace("phone:", "")
    text = _EXTENSION_PATTERN.sub("", text)
    text = text.split(";")[0]
    text = text.strip()
    if not text:
        return None
    if text.startswith("00"):
        text = "+" + text[2:]
    cleaned = re.sub(r"[^0-9+]+", "", text)
    if cleaned.startswith("00"):
        cleaned = "+" + cleaned[2:]
    has_plus = cleaned.startswith("+")
    digits = re.sub(r"\D", "", cleaned)
    if not digits:
        return None
    if has_plus:
        digits = "+" + digits
        if len(digits) < 4:
            return None
    else:
        if len(digits) < 7:
            return None
    return digits


def contact_dedup_key(email: Optional[str], phone: Optional[str]) -> Optional[str]:
    """Return a consistent deduplication key prioritizing email over phone."""
    normalized_email = normalize_email(email)
    if normalized_email:
        return f"email:{normalized_email}"
    normalized_phone = normalize_phone(phone)
    if normalized_phone:
        return f"phone:{normalized_phone}"
    return None