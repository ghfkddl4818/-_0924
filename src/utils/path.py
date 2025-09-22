from __future__ import annotations

from pathlib import Path
from typing import Union

PathLike = Union[str, Path]

__all__ = ["join_path", "normalize_path", "ensure_directory"]


def join_path(*parts: PathLike) -> Path:
    """Join *parts* into a single Path instance."""
    if not parts:
        raise ValueError("at least one path component is required")
    base = Path(parts[0])
    for part in parts[1:]:
        base /= Path(part)
    return base


def normalize_path(path: PathLike) -> Path:
    """Return an absolute, resolved Path for *path*."""
    return Path(path).expanduser().resolve()


def ensure_directory(path: PathLike) -> Path:
    """Ensure *path* exists as a directory and return it."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory
