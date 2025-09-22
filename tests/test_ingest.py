import pytest

from src.ingest.registry import Registry, RegistryEntry


def test_registry_adds_entry_and_tracks_robots_flag():
    registry = Registry()
    entry = registry.add(" https://example.com/resource ", respects_robots=False)

    assert isinstance(entry, RegistryEntry)
    assert entry.url == "https://example.com/resource"
    assert entry.respects_robots is False
    assert registry.exists("https://example.com/resource")
    assert registry.list_entries() == [entry]


def test_registry_prevents_duplicates():
    registry = Registry()
    registry.add("https://example.com/")

    with pytest.raises(ValueError):
        registry.add(" https://example.com/ ")

    assert registry.exists("https://example.com/")
    assert len(registry.list_entries()) == 1