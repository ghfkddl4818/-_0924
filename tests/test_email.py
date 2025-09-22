import pytest

from src.email.compose import EmailAdapter, EmailComposer, PromptRenderer, compose_email


VALID_META = (
    '{\n'
    '  "subject": "Signal ideas for {{company.name}}",\n'
    '  "cta": "Accept a 15 minute intro",\n'
    '  "language": "en",\n'
    '  "tone": "warm"\n'
    '}'
)

VALID_BODY = (
    "Hi {{contact.first_name}},\n\n"
    "I have been following the work that {{company.name}} is doing around privacy-preserving analytics, and your recent keynote about scaling responsible AI really resonated. "
    "We built RelayScope to give leaders like you clear telemetry across fragmented ops so teams can resolve incidents before customers even notice. "
    "In the pilot with Finch Robotics, engineers used the real-time dependency map to shrink diagnosis cycles by 37 percent and free up sprints for roadmap work.\n\n"
    "If you are open to it, I would love to share how other CTOs orchestrate observability without burning weekends. "
    "Are you available for a 15 minute chat next Tuesday morning? I can tailor the walkthrough around the systems you own today.\n\n"
    "Happy to send a short summary deck so you can preview the instrumentation stories your peers cite most often.\n\n"
    "Warm regards,\n"
    "{{sender.name}}"
)

VALID_OUTPUT = f"{VALID_META}\n\n{VALID_BODY}"


class StubBackend:
    def __init__(self, response: str) -> None:
        self._response = response
        self.prompts: list[str] = []

    def complete(self, prompt: str, **kwargs):
        self.prompts.append(prompt)
        return self._response


def test_email_composer_returns_valid_composition():
    data = {
        "contact": {"first_name": "Minji", "role": "CTO"},
        "company": {
            "name": "Atlas Labs",
            "focus": "privacy-preserving analytics",
            "signal": "Raised a Series B to expand infrastructure",
        },
        "product": {
            "value": "Reduce incident response times with observability automation",
            "proof": "Finch Robotics cut diagnosis cycles by 37%",
        },
        "sender": {"name": "Jay Park", "role": "Founder"},
    }
    backend = StubBackend(response=VALID_OUTPUT)
    composer = EmailComposer(backend=backend, prompt_renderer=PromptRenderer())

    composition = composer.compose(data, language="en")

    word_count = len(composition.body.split())
    assert 120 <= word_count <= 160
    assert composition.meta["tone"] == "warm"
    assert "{{contact.first_name}}" in composition.body
    assert "{{company.name}}" in composition.body
    assert backend.prompts, "backend should receive a prompt"
    assert "Atlas Labs" in backend.prompts[0]


def test_compose_email_wrapper_matches_composer():
    data = {
        "contact": {"first_name": "Minji", "role": "CTO"},
        "company": {
            "name": "Atlas Labs",
            "focus": "privacy-preserving analytics",
            "signal": "Raised a Series B to expand infrastructure",
        },
        "product": {
            "value": "Reduce incident response times with observability automation",
            "proof": "Finch Robotics cut diagnosis cycles by 37%",
        },
        "sender": {"name": "Jay Park", "role": "Founder"},
    }
    backend = StubBackend(response=VALID_OUTPUT)

    composition = compose_email(data, backend=backend, language="en")

    assert composition.meta["subject"].startswith("Signal ideas")
    assert composition.body.startswith("Hi {{contact.first_name}}")


def test_email_adapter_requires_multiple_tokens():
    adapter = EmailAdapter()
    body_with_single_token = VALID_BODY.replace("{{company.name}}", "Atlas Labs").replace(
        "{{sender.name}}", "Jay Park",
    )
    raw_output = f"{VALID_META}\n\n{body_with_single_token}"

    with pytest.raises(ValueError):
        adapter.adapt(raw_output)


def test_email_adapter_rejects_banned_phrases():
    adapter = EmailAdapter()
    raw_output = (
        f"{VALID_META}\n\n{VALID_BODY}\n"
        "This collaboration is a guaranteed win for {{company.name}}."
    )

    with pytest.raises(ValueError):
        adapter.adapt(raw_output)


def test_email_adapter_requires_meta_keys():
    adapter = EmailAdapter()
    invalid_meta = (
        '{\n'
        '  "subject": "Signal ideas for {{company.name}}",\n'
        '  "language": "en",\n'
        '  "tone": "warm"\n'
        '}'
    )
    raw_output = f"{invalid_meta}\n\n{VALID_BODY}"

    with pytest.raises(ValueError):
        adapter.adapt(raw_output)


def test_email_adapter_enforces_word_count():
    adapter = EmailAdapter()
    short_body = "Hi {{contact.first_name}}, this note is brief. Warm regards, {{sender.name}}."
    raw_output = f"{VALID_META}\n\n{short_body}"

    with pytest.raises(ValueError):
        adapter.adapt(raw_output)
