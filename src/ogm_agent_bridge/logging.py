"""Structured stderr logging with recursive secret redaction."""

from __future__ import annotations

import json
import logging
import sys
from collections.abc import Mapping
from typing import Any

_SECRET_KEYS = frozenset({"api_key", "authorization", "password", "secret", "token"})
_REDACTED = "[REDACTED]"


def redact_secrets(value: Any) -> Any:
    """Copy nested values while masking sensitive-key values."""
    if isinstance(value, Mapping):
        return {
            key: _REDACTED if key.lower() in _SECRET_KEYS else redact_secrets(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_secrets(item) for item in value)
    return value


class JsonFormatter(logging.Formatter):
    """Render log record fields as redacted JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        context = getattr(record, "context", {})
        if context:
            payload["context"] = context
        return json.dumps(redact_secrets(payload), default=str, sort_keys=True)


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure bridge logger writing JSON only to stderr."""
    logger = logging.getLogger("ogm_agent_bridge")
    logger.setLevel(level)
    logger.handlers.clear()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger
