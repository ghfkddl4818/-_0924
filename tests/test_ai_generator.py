from __future__ import annotations

from pathlib import Path

import pytest

from src.modules.ai_generator import AIGenerator


@pytest.fixture
def vertex_config(tmp_path: Path):
    template = tmp_path / "template.md"
    template.write_text("{product_name}", encoding="utf-8")
    return {
        "ai": {
            "provider": "vertex",
            "vertex": {
                "project_id": "demo-project",
                "location": "us-central1",
                "credentials_path": "",
                "model": {
                    "name": "gemini-2.5-pro",
                    "temperature": 0.55,
                    "max_output_tokens": 512,
                    "top_p": 0.9,
                },
            },
            "prompt": {
                "template_file": str(template),
                "language": "en",
                "schema": {"required": []},
            },
            "generation": {"retry_attempts": 1},
        },
        "ocr": {"tesseract": {"command": ""}},
    }


def _noop_log(*args, **kwargs) -> None:  # pragma: no cover - helper
    return None


def test_ai_generator_initialises_vertex(monkeypatch, vertex_config):
    captured = {}

    def fake_init(project: str, location: str, credentials):
        captured["init"] = (project, location, credentials)

    class DummyModel:
        def __init__(self, name: str) -> None:
            captured["model_name"] = name

        def generate_content(self, prompt: str, generation_config):
            captured["prompt"] = prompt
            captured["gen_config"] = generation_config
            return type("Resp", (), {"text": "hello"})()

    monkeypatch.setattr("src.modules.ai_generator.vertexai.init", fake_init)
    monkeypatch.setattr("src.modules.ai_generator.GenerativeModel", DummyModel)

    generator = AIGenerator(vertex_config, _noop_log)

    assert captured["init"] == ("demo-project", "us-central1", None)
    assert captured["model_name"] == "gemini-2.5-pro"
    assert generator._generation_kwargs["temperature"] == pytest.approx(0.55)
    assert generator._generation_kwargs["max_output_tokens"] == 512

    result = generator.call_llm("Say hi")

    assert result == "hello"
    assert captured["prompt"] == "Say hi"
    assert captured["gen_config"] is generator._generation_config


def test_ai_generator_extracts_candidate_text(monkeypatch, vertex_config):
    class DummyModel:
        def __init__(self, name: str) -> None:
            self.name = name

        def generate_content(self, prompt: str, generation_config):
            content = type("Content", (), {"parts": [type("Part", (), {"text": "foo"})(), type("Part", (), {"text": "bar"})()]})()
            candidate = type("Candidate", (), {"content": content})()
            return type("Resp", (), {"text": "", "candidates": [candidate]})()

    monkeypatch.setattr("src.modules.ai_generator.vertexai.init", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.modules.ai_generator.GenerativeModel", DummyModel)

    generator = AIGenerator(vertex_config, _noop_log)

    assert generator.call_llm("ignored") == "foobar"
