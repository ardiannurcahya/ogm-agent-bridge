"""B1 stdio MCP server."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from mcp.server.fastmcp import FastMCP

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.config import Settings, load_settings
from ogm_agent_bridge.errors import BridgeError
from ogm_agent_bridge.permissions import require_read

ToolHandler = Callable[[], Awaitable[dict[str, Any]]]


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


async def health(client: OGMClient) -> dict[str, Any]:
    """Call unauthenticated core health endpoint."""
    require_read("health")
    response = await client.request("GET", "/health", authenticated=False)
    return envelope(response.json())


def create_server(settings: Settings | None = None) -> FastMCP:
    """Create B1 MCP server."""
    resolved_settings = settings or load_settings()
    server = FastMCP("ogm-agent-bridge")

    @server.tool(description="Check OpenGraphMemory core liveness.")
    async def ogm_health() -> dict[str, Any]:
        try:
            async with OGMClient(resolved_settings) as client:
                return await health(client)
        except BridgeError as error:
            return safe_error(error)

    return server


def main() -> None:
    """Run MCP stdio server."""
    create_server().run(transport="stdio")
