"""Safe MCP tool response helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ogm_agent_bridge.errors import BridgeError


def envelope(
    data: Any,
    *,
    provenance: Mapping[str, Any] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Build common successful tool response."""
    return {
        "ok": True,
        "data": data,
        "provenance": dict(provenance or {}),
        "warnings": warnings or [],
    }


def safe_error(error: BridgeError) -> dict[str, Any]:
    """Build safe structured tool error."""
    return {
        "ok": False,
        "error": {"code": error.code, "message": str(error)},
    }
