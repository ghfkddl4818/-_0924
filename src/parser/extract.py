"""Parser utilities that convert vendor HTML into a normalized schema."""

from __future__ import annotations

import importlib.util
import sys
import re
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional

from bs4 import BeautifulSoup


def _load_rules_module():
    module_name = "_parser_rules_runtime"
    rules_path = Path(__file__).resolve().with_name("rules.py")
    spec = importlib.util.spec_from_file_location(module_name, rules_path)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_rules = _load_rules_module()
SelectorRule = _rules.SelectorRule
COMPANY_RULES = _rules.COMPANY_RULES
SUMMARY_RULES = _rules.SUMMARY_RULES
SERVICE_CONTAINER_SELECTORS = _rules.SERVICE_CONTAINER_SELECTORS
SERVICE_ITEM_SELECTORS = _rules.SERVICE_ITEM_SELECTORS
EMAIL_SELECTORS = _rules.EMAIL_SELECTORS
PHONE_SELECTORS = _rules.PHONE_SELECTORS
SERVICE_TEXT_SEPARATORS = _rules.SERVICE_TEXT_SEPARATORS
TITLE_SPLIT_MARKERS = _rules.TITLE_SPLIT_MARKERS

_EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_PHONE_PATTERN = re.compile(r"(\+?\d[\d\s().-]{6,}\d)")


@dataclass(slots=True)
class Parser:
    """HTML parser that extracts fields using a selector-first strategy."""

    def parse(self, html: str) -> dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")
        company = self._extract_company(soup)
        summary = self._extract_summary(soup)
        services = self._extract_services(soup)
        email = self._extract_email(soup)
        phone = self._extract_phone(soup)

        contact = {"email": email, "phone": phone}
        missing = self._collect_missing(company, services, summary, contact)

        return {
            "company": company,
            "services": services,
            "contact": contact,
            "summary": summary,
            "meta": {"missing": missing},
        }

    def _collect_missing(
        self,
        company: Optional[str],
        services: List[str],
        summary: Optional[str],
        contact: dict[str, Optional[str]],
    ) -> List[str]:
        missing: List[str] = []
        if not company:
            missing.append("company")
        if not services:
            missing.append("services")
        if not summary:
            missing.append("summary")
        if not contact.get("email"):
            missing.append("contact.email")
        if not contact.get("phone"):
            missing.append("contact.phone")
        return missing

    def _extract_company(self, soup: BeautifulSoup) -> Optional[str]:
        for rule in COMPANY_RULES:
            for node in soup.select(rule.selector):
                text = _node_text(node, rule.attribute, default_strip=rule.strip)
                if text:
                    return _normalize_company(text)
        return None

    def _extract_summary(self, soup: BeautifulSoup) -> Optional[str]:
        for rule in SUMMARY_RULES:
            for node in soup.select(rule.selector):
                text = _node_text(node, rule.attribute, default_strip=rule.strip)
                if text:
                    return text
        return None

    def _extract_services(self, soup: BeautifulSoup) -> List[str]:
        collected: List[str] = []
        for selector in SERVICE_CONTAINER_SELECTORS:
            for container in soup.select(selector):
                items = _service_items_from_container(container)
                collected.extend(items)
        if not collected:
            for selector in SERVICE_ITEM_SELECTORS:
                for node in soup.select(selector):
                    text = _node_text(node)
                    if text:
                        collected.append(text)
        return _dedupe_preserve_order(collected)

    def _extract_email(self, soup: BeautifulSoup) -> Optional[str]:
        for rule in EMAIL_SELECTORS:
            for node in soup.select(rule.selector):
                text = _node_text(node, rule.attribute)
                text = _normalize_contact_value(text)
                if text and _EMAIL_PATTERN.fullmatch(text):
                    return text
                # Allow mailto href fallthrough when attribute has prepended scheme.
                if text and text.startswith("mailto:"):
                    candidate = text.split(":", 1)[1]
                    if _EMAIL_PATTERN.fullmatch(candidate):
                        return candidate
        # Fallback: scan body text for first email.
        match = _EMAIL_PATTERN.search(soup.get_text(" ", strip=True))
        if match:
            return match.group(0)
        return None

    def _extract_phone(self, soup: BeautifulSoup) -> Optional[str]:
        for rule in PHONE_SELECTORS:
            for node in soup.select(rule.selector):
                text = _node_text(node, rule.attribute)
                text = _normalize_contact_value(text)
                if text:
                    text = text.replace("tel:", "")
                    match = _PHONE_PATTERN.search(text)
                    if match:
                        return _clean_phone(match.group(1))
        match = _PHONE_PATTERN.search(soup.get_text(" ", strip=True))
        if match:
            return _clean_phone(match.group(1))
        return None


def _node_text(node: Any, attribute: Optional[str] = None, default_strip: bool = True) -> str:
    if attribute:
        value = node.get(attribute, "")
        return value.strip() if isinstance(value, str) else ""
    text = node.get_text(" ") if hasattr(node, "get_text") else ''
    return text.strip() if default_strip else text


def _normalize_company(text: str) -> str:
    for marker in TITLE_SPLIT_MARKERS:
        if marker in text:
            text = text.split(marker, 1)[0]
    return text.strip()


def _service_items_from_container(container: Any) -> List[str]:
    texts: List[str] = []
    items = container.select("li") if hasattr(container, "select") else []
    if items:
        for item in items:
            text = _node_text(item)
            if text:
                texts.append(text)
    else:
        text = _node_text(container)
        texts.extend(_split_services_text(text))
    return texts


def _split_services_text(text: str) -> List[str]:
    working = text
    for sep in SERVICE_TEXT_SEPARATORS:
        working = working.replace(sep, "\n")
    parts = [segment.strip() for segment in working.split("\n")]
    return [segment for segment in parts if segment]


def _dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    return list(OrderedDict.fromkeys(item.strip() for item in items if item.strip()))


def _normalize_contact_value(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    cleaned = value.strip()
    return cleaned or None


def _clean_phone(value: str) -> str:
    digits = re.sub(r"[^0-9+]+", " ", value).split()
    return " ".join(digits)


__all__ = ["Parser"]
