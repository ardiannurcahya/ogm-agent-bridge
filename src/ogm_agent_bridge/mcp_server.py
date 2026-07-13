"""B1 stdio MCP server."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.config import Settings, load_settings
from ogm_agent_bridge.errors import BridgeError
from ogm_agent_bridge.permissions import require_read
from ogm_agent_bridge.responses import envelope, safe_error
from ogm_agent_bridge.tools import list_datasets
from ogm_agent_bridge.tools import query as run_query


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

    @server.tool(description="List datasets visible in configured project.")
    async def ogm_list_datasets() -> dict[str, Any]:
        try:
            async with OGMClient(resolved_settings) as client:
                return await list_datasets(client)
        except BridgeError as error:
            return safe_error(error)

    @server.tool(description="Run grounded OpenGraphMemory retrieval.")
    async def ogm_query(dataset_id: str, query: str, **options: Any) -> dict[str, Any]:
        try:
            arguments = {"dataset_id": dataset_id, "query": query, **options}
            async with OGMClient(resolved_settings) as client:
                return await run_query(client, arguments)
        except BridgeError as error:
            return safe_error(error)

    return server


def main() -> None:
    """Run MCP stdio server."""
    create_server().run(transport="stdio")
