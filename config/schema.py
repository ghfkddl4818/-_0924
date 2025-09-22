from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

ENV_PREFIX = "UAS_"
ENV_SEPARATOR = "__"
DEFAULT_CONFIG_PATH = Path(__file__).with_name("default.yaml")


class SystemConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str = Field(default="3.0.0")
    debug_mode: bool = False
    test_mode: bool = False


class PathsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    root_dir: Path = Field(default_factory=lambda: Path("."))
    download_folder: Path = Field(default_factory=lambda: Path("./downloads"))
    log_folder: Path = Field(default_factory=lambda: Path("./logs"))
    output_folder: Path = Field(default_factory=lambda: Path("./outputs"))


class ModelSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str
    temperature: float = 0.3
    max_tokens: int = 1000


class AIConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: str
    api_key: str | None = None
    models: dict[str, ModelSettings]


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    level: str = "INFO"
    format: str = "[%(asctime)s][%(name)s][%(levelname)s] %(message)s"
    file_rotation: str = "daily"


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    system: SystemConfig
    paths: PathsConfig
    ai: AIConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def _set_nested(container: dict[str, Any], keys: list[str], value: Any) -> None:
    key = keys[0]
    if len(keys) == 1:
        container[key] = value
        return
    child = container.setdefault(key, {})
    if not isinstance(child, dict):
        container[key] = {}
        child = container[key]
    _set_nested(child, keys[1:], value)


def _deep_merge(base: dict[str, Any], overrides: Mapping[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in overrides.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, Mapping)
        ):
            merged[key] = _deep_merge(merged[key], value)  # type: ignore[arg-type]
        else:
            merged[key] = value
    return merged


def _collect_env_overrides(env: Mapping[str, str]) -> dict[str, Any]:
    collected: dict[str, Any] = {}
    for raw_key, raw_value in env.items():
        if not raw_key.startswith(ENV_PREFIX):
            continue
        path = raw_key.removeprefix(ENV_PREFIX)
        if not path:
            continue
        keys = [segment.lower() for segment in path.split(ENV_SEPARATOR) if segment]
        if not keys:
            continue
        try:
            parsed_value: Any = yaml.safe_load(raw_value)
        except yaml.YAMLError:
            parsed_value = raw_value
        _set_nested(collected, keys, parsed_value)
    return collected


def load_config(
    config_path: str | Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> AppConfig:
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    overrides = _collect_env_overrides(env or os.environ)
    merged = _deep_merge(data, overrides)
    return AppConfig.model_validate(merged)


__all__ = ["AppConfig", "load_config"]