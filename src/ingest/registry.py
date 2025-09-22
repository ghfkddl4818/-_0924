from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    """Represents an ingest target and whether it respects robots.txt policies."""

    url: str
    respects_robots: bool = True


class Registry:
    """In-memory registry for ingest targets with duplicate protection."""

    def __init__(self) -> None:
        self._entries: Dict[str, RegistryEntry] = {}

    def add(self, url: str, *, respects_robots: bool = True) -> RegistryEntry:
        """Register a new URL and store whether it respects robots rules."""

        normalized = self._normalize_url(url)
        if normalized in self._entries:
            raise ValueError(f"URL already registered: {normalized}")

        entry = RegistryEntry(url=normalized, respects_robots=respects_robots)
        self._entries[normalized] = entry
        return entry

    def exists(self, url: str) -> bool:
        """Return True when the URL has already been registered."""

        normalized = self._normalize_url(url)
        return normalized in self._entries

    def list_entries(self) -> List[RegistryEntry]:
        """Return all registered entries preserving insertion order."""

        return list(self._entries.values())

    @staticmethod
    def _normalize_url(url: str) -> str:
        if not isinstance(url, str):
            raise ValueError("URL must be provided as a string")

        normalized = url.strip()
        if not normalized:
            raise ValueError("URL must be a non-empty string")
        return normalized


_registry = Registry()


def add(url: str, *, respects_robots: bool = True) -> RegistryEntry:
    """Add the URL to the default registry."""

    return _registry.add(url, respects_robots=respects_robots)


def exists(url: str) -> bool:
    """Check whether the URL is present in the default registry."""

    return _registry.exists(url)


def list_entries() -> List[RegistryEntry]:
    """Expose the default registry entries."""

    return _registry.list_entries()