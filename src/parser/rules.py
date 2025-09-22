"""Reusable extraction rules for the HTML company parser."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass(frozen=True)
class SelectorRule:
    """Selector definition with optional attribute extraction."""

    selector: str
    attribute: Optional[str] = None
    strip: bool = True


# Split characters to separate compound text such as "Brand - Tagline".
TITLE_SPLIT_MARKERS: Sequence[str] = ("|", "-", "•", "—", ":")

# First non-empty selector wins for each category.
COMPANY_RULES: Sequence[SelectorRule] = (
    SelectorRule('meta[property="og:site_name"]', attribute="content"),
    SelectorRule('meta[name="application-name"]', attribute="content"),
    SelectorRule('meta[name="twitter:title"]', attribute="content"),
    SelectorRule('meta[property="og:title"]', attribute="content"),
    SelectorRule('header .company-name'),
    SelectorRule('header h1'),
    SelectorRule('main .company-name'),
    SelectorRule('section.hero h1'),
    SelectorRule('h1'),
    SelectorRule('title', strip=False),
)

SUMMARY_RULES: Sequence[SelectorRule] = (
    SelectorRule('meta[name="description"]', attribute="content"),
    SelectorRule('meta[property="og:description"]', attribute="content"),
    SelectorRule('section.summary p'),
    SelectorRule('.summary p'),
    SelectorRule('.summary'),
    SelectorRule('section.hero p'),
    SelectorRule('main p'),
)

SERVICE_CONTAINER_SELECTORS: Sequence[str] = (
    '#services',
    '[data-section="services"]',
    'section.services',
    '.services-list',
    '.services',
    '.what-we-do',
    '.capabilities',
)

SERVICE_ITEM_SELECTORS: Sequence[str] = (
    'li.service-item',
    '.services li',
    '.service',
    '.capabilities li',
    '.offerings li',
    '.what-we-do li',
    'li',
)

EMAIL_SELECTORS: Sequence[SelectorRule] = (
    SelectorRule('a[href^="mailto:"]', attribute="href"),
    SelectorRule('[data-contact-email]'),
    SelectorRule('.email a'),
    SelectorRule('.email'),
    SelectorRule('.contact a[href^="mailto:"]', attribute="href"),
    SelectorRule('.contact .email'),
)

PHONE_SELECTORS: Sequence[SelectorRule] = (
    SelectorRule('a[href^="tel:"]', attribute="href"),
    SelectorRule('.phone a', attribute="href"),
    SelectorRule('.phone'),
    SelectorRule('.contact .phone'),
    SelectorRule('[data-contact-phone]'),
)

SERVICE_TEXT_SEPARATORS: Sequence[str] = ("\n", "|", ",", ";")
