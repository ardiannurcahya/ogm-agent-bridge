"""Hardcoded B1 read permissions."""

from __future__ import annotations

from ogm_agent_bridge.errors import PermissionError

_READ_PERMISSIONS = frozenset({"health", "datasets:read", "graph:read"})


def require_read(permission: str) -> None:
    """Allow only registered graph-first read permissions."""
    if permission not in _READ_PERMISSIONS:
        raise PermissionError("Tool permission denied")


def require_write(profile: str, permission: str) -> None:
    """Allow safe uploads only in personal-safe profile."""
    if profile != "personal-safe" or permission != "documents:write":
        raise PermissionError("Tool permission denied")
