from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable
from zipfile import ZIP_DEFLATED, ZipFile

ArchiveFactory = Callable[[Path], ZipFile]
Clock = Callable[[], datetime]


def create_failure_pack(
    inputs: Path | str | None,
    intermediates: Path | str | None,
    outputs: Path | str | None,
    destination: Path | str,
    *,
    zip_factory: ArchiveFactory | None = None,
    clock: Clock | None = None,
) -> Path:
    """Bundle inputs, intermediates, and outputs into a single archive."""

    archive_path = Path(destination)
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    factory = zip_factory or _default_zip_factory
    now = clock or (lambda: datetime.now(timezone.utc))

    sections = [
        ("inputs", _optional_path(inputs)),
        ("intermediate", _optional_path(intermediates)),
        ("outputs", _optional_path(outputs)),
    ]

    manifest: dict[str, object] = {
        "generated_at": now().isoformat(),
        "sections": {},
    }

    with factory(archive_path) as archive:
        for name, root in sections:
            archived_files = []
            if root is not None and root.exists():
                for file_path in _iter_files(root):
                    arcname = Path(name) / file_path.relative_to(root)
                    arcname_str = arcname.as_posix()
                    if file_path.suffix in {".log", ".txt", ".json", ".yaml", ".yml", ""}:
                        _write_text_entry(archive, file_path, arcname_str)
                    else:
                        try:
                            text = file_path.read_text(encoding="utf-8")
                        except (UnicodeDecodeError, OSError):
                            archive.write(file_path, arcname_str)
                        else:
                            _write_text_entry(archive, file_path, arcname_str, text)
                    archived_files.append(arcname_str)
            manifest["sections"][name] = archived_files
        archive.writestr(
            "manifest.json",
            json.dumps(manifest, indent=2, ensure_ascii=False),
        )

    return archive_path


def _iter_files(root: Path) -> Iterable[Path]:
    for candidate in sorted(root.rglob("*")):
        if candidate.is_file():
            yield candidate


def _optional_path(value: Path | str | None) -> Path | None:
    if value is None:
        return None
    return Path(value)


def _default_zip_factory(path: Path) -> ZipFile:
    return ZipFile(path, mode="w", compression=ZIP_DEFLATED)


def _write_text_entry(
    archive: ZipFile,
    file_path: Path,
    arcname: str,
    text: str | None = None,
) -> None:
    try:
        content = text if text is not None else file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        archive.write(file_path, arcname)
        return
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    archive.writestr(arcname, normalized)


__all__ = ["create_failure_pack"]
