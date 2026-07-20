"""Hardcoded bridge capability profiles."""

from __future__ import annotations

from ogm_agent_bridge.errors import PermissionError

_READ_PERMISSIONS = frozenset(
    {"health", "datasets:read", "graph:read", "agent-memory:read"}
)


def require_read(permission: str) -> None:
    """Allow only registered read permissions."""
    if permission not in _READ_PERMISSIONS:
        raise PermissionError("Tool permission denied")


def require_memory_read() -> None:
    require_read("agent-memory:read")


def require_write(profile: str, permission: str) -> None:
    """Allow reviewed writes in the appropriate profile."""
    if profile != "personal-safe" or permission != "documents:write":
        raise PermissionError("Tool permission denied")


def require_memory_write(profile: str, permission: str) -> None:
    """Allow additive writes to personal-safe and curation to memory-curator."""
    if permission == "agent-memory:write" and profile in {
        "personal-safe",
        "memory-curator",
    }:
        return
    if permission == "agent-memory:curate" and profile == "memory-curator":
        return
    if permission not in {"agent-memory:write", "agent-memory:curate"}:
        raise PermissionError("Tool permission denied")
    raise PermissionError("Tool permission denied")
