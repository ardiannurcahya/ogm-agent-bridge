"""Hardcoded B1 read permissions."""

from __future__ import annotations

from ogm_agent_bridge.errors import PermissionError

_READ_PERMISSIONS = frozenset(
    {"health", "datasets:read", "query:read", "memory:read", "graph:read"}
)


def require_read(permission: str) -> None:
    """Allow only registered B1 read permissions."""
    if permission not in _READ_PERMISSIONS:
        raise PermissionError("Tool permission denied")


def require_write(profile: str, permission: str) -> None:
    """Allow B2 safe writes only in personal-safe profile."""
    if profile != "personal-safe" or permission not in {
        "memory:write",
        "documents:write",
    }:
        raise PermissionError("Tool permission denied")
