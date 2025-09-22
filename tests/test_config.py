from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from config.schema import AppConfig, load_config


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "default.yaml"


def test_load_config_uses_defaults() -> None:
    config = load_config(env={})

    assert isinstance(config, AppConfig)
    assert config.system.version == "3.0.0"
    assert config.ai.models["gemini"].temperature == 0.3
    assert config.logging.level == "INFO"


def test_load_config_rejects_unknown_keys(tmp_path: Path) -> None:
    data = yaml.safe_load(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
    data["system"]["unexpected"] = True
    bad_path = tmp_path / "bad.yaml"
    bad_path.write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_config(bad_path, env={})


def test_environment_overrides_are_applied() -> None:
    env = {
        "UAS_SYSTEM__DEBUG_MODE": "true",
        "UAS_AI__MODELS__GEMINI__TEMPERATURE": "0.7",
    }

    config = load_config(env=env)

    assert config.system.debug_mode is True
    assert config.ai.models["gemini"].temperature == pytest.approx(0.7)