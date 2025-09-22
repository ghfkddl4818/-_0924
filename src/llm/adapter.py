"""LLM backend abstractions and concrete integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any, Protocol


class CompletionClient(Protocol):
    """Protocol describing the minimal completion client contract."""

    def create_completion(self, **kwargs: Any) -> Mapping[str, Any]:
        ...


class LLMBackend(ABC):
    """Common interface for large language model backends."""

    @abstractmethod
    def complete(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        stop: Sequence[str] | None = None,
        max_tokens: int | None = None,
        **extra: Any,
    ) -> str:
        """Generate a completion for the supplied prompt."""
        ...


class CodexBackend(LLMBackend):
    """Adapter around a Codex-style completion endpoint."""

    def __init__(self, client: CompletionClient, model: str) -> None:
        self._client = client
        self._model = model

    def complete(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        stop: Sequence[str] | None = None,
        max_tokens: int | None = None,
        **extra: Any,
    ) -> str:
        payload = self._build_payload(
            prompt=prompt,
            temperature=temperature,
            stop=stop,
            max_tokens=max_tokens,
            extra=extra,
        )
        response = self._client.create_completion(**payload)
        return self._extract_text(response)

    def _build_payload(
        self,
        *,
        prompt: str,
        temperature: float | None,
        stop: Sequence[str] | None,
        max_tokens: int | None,
        extra: dict[str, Any],
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"model": self._model, "prompt": prompt}

        if temperature is not None:
            if not isinstance(temperature, (int, float)):
                raise ValueError("temperature must be numeric")
            temperature_value = float(temperature)
            if not 0 <= temperature_value <= 2:
                raise ValueError("temperature must be between 0 and 2")
            payload["temperature"] = temperature_value

        if max_tokens is not None:
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                raise ValueError("max_tokens must be a positive integer")
            payload["max_tokens"] = max_tokens

        if stop is not None:
            if isinstance(stop, str):
                raise ValueError("stop must be a sequence of strings")
            stop_list = list(stop)
            if not all(isinstance(token, str) for token in stop_list):
                raise ValueError("stop must contain only strings")
            payload["stop"] = stop_list

        payload.update({k: v for k, v in extra.items() if v is not None})
        return payload

    @staticmethod
    def _extract_text(response: Mapping[str, Any]) -> str:
        choices = response.get("choices")
        if (
            isinstance(choices, Sequence)
            and not isinstance(choices, (str, bytes))
            and choices
        ):
            first = choices[0]
            if isinstance(first, Mapping) and "text" in first:
                return str(first["text"])
        return ""


class ChatBackend(LLMBackend):
    """Placeholder for a chat-completions backend."""

    def complete(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        stop: Sequence[str] | None = None,
        max_tokens: int | None = None,
        **extra: Any,
    ) -> str:
        raise NotImplementedError("ChatBackend is not implemented yet")
