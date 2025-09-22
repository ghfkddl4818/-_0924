import pytest

from src.llm.adapter import CodexBackend


class DummyClient:
    def __init__(self) -> None:
        self.last_payload = None

    def create_completion(self, **kwargs):
        self.last_payload = kwargs
        return {"choices": [{"text": "hello"}]}


def test_codex_backend_serializes_optional_parameters():
    client = DummyClient()
    backend = CodexBackend(client=client, model="code-davinci-002")

    result = backend.complete(
        "Generate code",
        temperature=0.3,
        stop=("###",),
        max_tokens=120,
    )

    assert result == "hello"
    assert client.last_payload["model"] == "code-davinci-002"
    assert client.last_payload["prompt"] == "Generate code"
    assert client.last_payload["temperature"] == pytest.approx(0.3)
    assert client.last_payload["stop"] == ["###"]
    assert client.last_payload["max_tokens"] == 120


def test_codex_backend_omits_none_values():
    client = DummyClient()
    backend = CodexBackend(client=client, model="code-davinci-002")

    backend.complete("Say hello")

    assert "temperature" not in client.last_payload
    assert "stop" not in client.last_payload
    assert "max_tokens" not in client.last_payload


@pytest.mark.parametrize("temperature", [-0.1, 2.5])
def test_codex_backend_validates_temperature_range(temperature):
    backend = CodexBackend(client=DummyClient(), model="code-davinci-002")

    with pytest.raises(ValueError):
        backend.complete("Test", temperature=temperature)


def test_codex_backend_rejects_invalid_stop_sequence():
    backend = CodexBackend(client=DummyClient(), model="code-davinci-002")

    with pytest.raises(ValueError):
        backend.complete("Test", stop=[123])

    with pytest.raises(ValueError):
        backend.complete("Test", stop="END")


def test_codex_backend_requires_positive_max_tokens():
    backend = CodexBackend(client=DummyClient(), model="code-davinci-002")

    with pytest.raises(ValueError):
        backend.complete("Test", max_tokens=0)
