"""Configuration loading for bridge process."""

from __future__ import annotations

import math
import os
import uuid
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
    permission_profile: str = "read-only"
    upload_roots: tuple[Path, ...] = ()

    def __post_init__(self) -> None:
        """Keep direct Settings construction as strict as environment loading."""
        if (
            not math.isfinite(self.timeout_seconds)
            or not 0 < self.timeout_seconds <= _MAX_TIMEOUT_SECONDS
        ):
            raise ConfigError("timeout_seconds must be finite, positive, and bounded")
        if (
            type(self.max_retries) is not int
            or not 0 <= self.max_retries <= _MAX_RETRIES
        ):
            raise ConfigError("max_retries must be a bounded non-negative integer")


_MAX_TIMEOUT_SECONDS = 120.0
_MAX_RETRIES = 5


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
    try:
        uuid.UUID(project_id)
    except ValueError as error:
        raise ConfigError("OGM_PROJECT_ID must be a UUID") from error
    profile = environ.get("OGM_PERMISSION_PROFILE", "read-only")
    if profile not in {"read-only", "personal-safe", "memory-curator"}:
        raise ConfigError(
            "OGM_PERMISSION_PROFILE must be read-only, personal-safe, or memory-curator"
        )
    return Settings(
        base_url,
        api_key,
        project_id,
        _positive_float(environ, "OGM_TIMEOUT_SECONDS", 30.0),
        _nonnegative_int(environ, "OGM_MAX_RETRIES", 2),
        profile,
        _upload_roots(environ),
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
    if not math.isfinite(value):
        raise ConfigError(f"{name} must be finite")
    if value <= 0:
        raise ConfigError(f"{name} must be positive")
    if value > _MAX_TIMEOUT_SECONDS:
        raise ConfigError(f"{name} must not exceed {_MAX_TIMEOUT_SECONDS:g}")
    return value


def _upload_roots(environ: Mapping[str, str]) -> tuple[Path, ...]:
    raw = environ.get("OGM_UPLOAD_ROOTS")
    if raw is None:
        return ()
    roots = raw.split(os.pathsep)
    if not all(roots):
        raise ConfigError("OGM_UPLOAD_ROOTS must not contain empty paths")
    return tuple(Path(root).expanduser().resolve() for root in roots)


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
    if value > _MAX_RETRIES:
        raise ConfigError(f"{name} must not exceed {_MAX_RETRIES}")
    return value
