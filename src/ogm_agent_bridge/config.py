"""Configuration loading for bridge process."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class ConfigError(ValueError):
    """Raised when required configuration is invalid or missing."""


@dataclass(frozen=True, slots=True)
class Settings:
    base_url: str
    api_key: str
    project_id: str
    timeout_seconds: float = 30.0
    max_retries: int = 2
    state_db: Path = Path("~/.local/state/ogm-agent-bridge/state.db")
    permission_profile: str = "personal-safe"


def load_settings(
    environ: Mapping[str, str] | None = None, *, dotenv_path: Path | None = None
) -> Settings:
    """Load settings from environment after optional local .env file."""
    if environ is None:
        load_dotenv(dotenv_path=dotenv_path, override=False)
        environ = os.environ
    base_url = _required(environ, "OGM_BASE_URL").rstrip("/")
    api_key = _required(environ, "OGM_API_KEY")
    project_id = _required(environ, "OGM_PROJECT_ID")
    profile = environ.get("OGM_PERMISSION_PROFILE", "personal-safe")
    if profile not in {"read-only", "personal-safe"}:
        raise ConfigError("OGM_PERMISSION_PROFILE must be read-only or personal-safe")
    return Settings(
        base_url,
        api_key,
        project_id,
        _positive_float(environ, "OGM_TIMEOUT_SECONDS", 30.0),
        _nonnegative_int(environ, "OGM_MAX_RETRIES", 2),
        Path(
            environ.get("OGM_STATE_DB", "~/.local/state/ogm-agent-bridge/state.db")
        ).expanduser(),
        profile,
    )


def _required(environ: Mapping[str, str], name: str) -> str:
    value = environ.get(name, "").strip()
    if not value:
        raise ConfigError(f"{name} is required")
    return value


def _positive_float(environ: Mapping[str, str], name: str, default: float) -> float:
    raw = environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError as error:
        raise ConfigError(f"{name} must be a number") from error
    if value <= 0:
        raise ConfigError(f"{name} must be positive")
    return value


def _nonnegative_int(environ: Mapping[str, str], name: str, default: int) -> int:
    raw = environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as error:
        raise ConfigError(f"{name} must be an integer") from error
    if value < 0:
        raise ConfigError(f"{name} must be non-negative")
    return value
