import json
import logging

from ogm_agent_bridge.logging import JsonFormatter, redact_secrets


def test_redacts_nested_secrets() -> None:
    value = {"api_key": "key-123", "nested": [{"token": "token-456"}]}

    assert redact_secrets(value) == {
        "api_key": "[REDACTED]",
        "nested": [{"token": "[REDACTED]"}],
    }


def test_formatter_never_emits_secret() -> None:
    record = logging.LogRecord(
        "ogm_agent_bridge", logging.INFO, "", 0, "request", (), None
    )
    record.context = {"authorization": "Bearer secret-123", "path": "/health"}

    rendered = JsonFormatter().format(record)

    assert "secret-123" not in rendered
    assert json.loads(rendered)["context"]["authorization"] == "[REDACTED]"
