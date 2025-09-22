from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class BrowserClient(Protocol):
    """Interface stub describing the browser automation surface."""

    def open(self, url: str) -> None:
        ...

    def execute(self, script: str) -> str:
        ...

    def screenshot(self) -> bytes:
        ...

    def close(self) -> None:
        ...