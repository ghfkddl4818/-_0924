"""Utilities for composing cold outreach emails via the LLM pipeline."""

from __future__ import annotations

import json
import re
import string
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.llm.adapter import LLMBackend

DEFAULT_TEMPLATE_ROOT = Path(__file__).resolve().parents[2] / "templates" / "email"


class _DotFormatter(string.Formatter):
    """Formatter that understands dotted placeholders against nested mappings."""

    def __init__(self, data: Mapping[str, Any]):
        self._data = data

    def get_field(self, field_name: Any, args: Sequence[Any], kwargs: Mapping[str, Any]):  # type: ignore[override]
        if isinstance(field_name, str):
            return self._lookup(field_name), field_name
        return super().get_field(field_name, args, kwargs)

    def _lookup(self, path: str) -> Any:
        value: Any = self._data
        for part in path.split('.'):  # support dotted access e.g. contact.first_name
            if isinstance(value, Mapping) and part in value:
                value = value[part]
            else:
                return ""
        if value is None:
            return ""
        if isinstance(value, (str, int, float)):
            return value
        return json.dumps(value, ensure_ascii=False)


class PromptRenderer:
    """Load and render prompt templates with provided data."""

    def __init__(self, template_root: Path | None = None, template_name: str = "cold.md") -> None:
        self._template_root = Path(template_root) if template_root else DEFAULT_TEMPLATE_ROOT
        self._template_name = template_name

    def render(self, data: Mapping[str, Any], *, language: str = "en") -> str:
        template_path = self._template_root / language / self._template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found for language '{language}': {template_path}")
        template = template_path.read_text(encoding="utf-8")
        formatter = _DotFormatter(data)
        return formatter.format(template)


@dataclass(frozen=True)
class EmailComposition:
    body: str
    meta: dict[str, Any]


class EmailAdapter:
    """Convert LLM raw output into structured email content with validation."""

    def __init__(
        self,
        *,
        required_meta_keys: Sequence[str] | None = None,
        banned_phrases: Sequence[str] | None = None,
        personalization_tokens: Sequence[str] | None = None,
        allowed_tones: Sequence[str] | None = None,
        min_word_count: int = 120,
        max_word_count: int = 160,
    ) -> None:
        self._required_meta_keys = tuple(required_meta_keys or ("subject", "cta", "tone", "language"))
        self._banned_phrases = {phrase.lower() for phrase in (banned_phrases or ("free money", "guaranteed win", "no obligation"))}
        self._personalization_tokens = tuple(personalization_tokens or ("{{contact.first_name}}", "{{company.name}}", "{{sender.name}}"))
        self._allowed_tones = {tone.lower() for tone in (allowed_tones or ("warm", "friendly", "professional"))}
        self._min_word_count = min_word_count
        self._max_word_count = max_word_count

    def adapt(self, raw: str) -> EmailComposition:
        meta, body = self._extract_raw_sections(raw)
        self._validate_meta(meta)
        self._validate_body(body)
        return EmailComposition(body=body, meta=meta)

    def _extract_raw_sections(self, raw: str) -> tuple[dict[str, Any], str]:
        if not raw or not raw.strip():
            raise ValueError("LLM output is empty")
        raw = raw.strip()
        decoder = json.JSONDecoder()
        try:
            meta, end = decoder.raw_decode(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Meta section must start with a JSON object") from exc
        if not isinstance(meta, dict):
            raise ValueError("Meta section must be a JSON object")
        body = raw[end:].strip()
        if not body:
            raise ValueError("Email body is missing")
        return meta, body

    def _validate_meta(self, meta: dict[str, Any]) -> None:
        missing = [key for key in self._required_meta_keys if not meta.get(key)]
        if missing:
            raise ValueError(f"Meta is missing required keys: {', '.join(missing)}")
        tone = str(meta.get("tone", "")).strip().lower()
        if tone not in self._allowed_tones:
            raise ValueError("Tone is not allowed")

    def _validate_body(self, body: str) -> None:
        words = re.findall(r"[\w'-]+", body)
        word_count = len(words)
        if word_count < self._min_word_count or word_count > self._max_word_count:
            raise ValueError("Email body must be between 120 and 160 words")
        occurrences = sum(body.count(token) for token in self._personalization_tokens)
        if occurrences < 2:
            raise ValueError("Email body must include at least two personalization tokens")
        lowered = body.lower()
        for phrase in self._banned_phrases:
            if phrase in lowered:
                raise ValueError("Email body contains banned language")


class EmailComposer:
    """High-level orchestration for the data → prompt → adapter pipeline."""

    def __init__(
        self,
        backend: LLMBackend,
        prompt_renderer: PromptRenderer | None = None,
        adapter: EmailAdapter | None = None,
    ) -> None:
        self._backend = backend
        self._prompt_renderer = prompt_renderer or PromptRenderer()
        self._adapter = adapter or EmailAdapter()

    def compose(self, data: Mapping[str, Any], *, language: str = "en") -> EmailComposition:
        prompt = self._prompt_renderer.render(data, language=language)
        raw = self._backend.complete(prompt)
        return self._adapter.adapt(raw)


def compose_email(
    data: Mapping[str, Any],
    *,
    backend: LLMBackend,
    language: str = "en",
    prompt_renderer: PromptRenderer | None = None,
    adapter: EmailAdapter | None = None,
) -> EmailComposition:
    """Convenience wrapper returning the composed email body and meta."""

    composer = EmailComposer(
        backend=backend,
        prompt_renderer=prompt_renderer,
        adapter=adapter,
    )
    return composer.compose(data, language=language)
