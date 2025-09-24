"""Helper utilities for assembling diagnostic bug packs."""

from __future__ import annotations

import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional

import yaml


def collect_bugpack(
    config: Dict,
    logger: Callable[[str, str], None],
    reason: str,
    extras: Optional[Iterable[Path | str]] = None,
) -> Optional[Path]:
    """Collect logs, screenshots and configuration snapshots into a zip file."""

    paths_conf = config.get("paths", {})
    bugpack_dir = Path(paths_conf.get("bugpack_folder", "./runs")).expanduser()
    bugpack_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = bugpack_dir / f"bugpack_{timestamp}.zip"
    screenshot_path: Optional[Path] = None

    try:
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            _write_reason(zf, reason)
            _write_logs(zf, paths_conf)
            _write_config_snapshot(zf, config)
            screenshot_path = _capture_screenshot(zf, timestamp, logger)
            _write_extras(zf, extras)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger("ERROR", f"버그팩 생성 실패: {exc}")
        return None
    finally:
        if screenshot_path and screenshot_path.exists():
            screenshot_path.unlink(missing_ok=True)

    logger("INFO", f"버그팩 생성 완료: {archive_path}")
    return archive_path


def _write_reason(zf: zipfile.ZipFile, reason: str) -> None:
    payload = f"reason: {reason}\n"
    zf.writestr("bugpack/reason.txt", payload)


def _write_logs(zf: zipfile.ZipFile, paths_conf: Dict) -> None:
    log_folder = Path(paths_conf.get("log_folder", "./logs")).expanduser()
    if not log_folder.exists():
        return
    for path in log_folder.rglob("*"):
        if path.is_file():
            arc = Path("bugpack/logs") / path.relative_to(log_folder)
            zf.write(path, arc.as_posix())


def _write_config_snapshot(zf: zipfile.ZipFile, config: Dict) -> None:
    config_path = Path("config/config.yaml")
    if config_path.exists():
        zf.write(config_path, "bugpack/config/config.yaml")
    snapshot = yaml.safe_dump(config, allow_unicode=True, sort_keys=False)
    zf.writestr("bugpack/config/runtime_snapshot.yaml", snapshot)
    zf.writestr("bugpack/config/runtime_snapshot.json", json.dumps(config, ensure_ascii=False, indent=2))


def _capture_screenshot(zf: zipfile.ZipFile, timestamp: str, logger: Callable[[str, str], None]) -> Optional[Path]:
    try:
        import pyautogui

        shot_path = Path("./runs") / f"screenshot_{timestamp}.png"
        shot_path.parent.mkdir(parents=True, exist_ok=True)
        image = pyautogui.screenshot()
        image.save(shot_path)
        zf.write(shot_path, f"bugpack/{shot_path.name}")
        return shot_path
    except Exception as exc:  # pragma: no cover - screen capture might fail on CI
        logger("WARNING", f"버그팩 스크린샷 수집 실패: {exc}")
        return None


def _write_extras(zf: zipfile.ZipFile, extras: Optional[Iterable[Path | str]]) -> None:
    if not extras:
        return
    for extra in extras:
        path = Path(extra)
        if not path.exists():
            continue
        if path.is_file():
            arc = Path("bugpack/extra") / path.name
            zf.write(path, arc.as_posix())
        else:
            for sub in path.rglob("*"):
                if sub.is_file():
                    arc = Path("bugpack/extra") / sub.relative_to(path)
                    zf.write(sub, arc.as_posix())
