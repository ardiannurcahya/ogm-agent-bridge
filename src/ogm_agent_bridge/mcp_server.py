"""B1 stdio MCP server."""

from __future__ import annotations

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.config import Settings, load_settings
from ogm_agent_bridge.errors import BridgeError
from ogm_agent_bridge.permissions import require_read
from ogm_agent_bridge.responses import envelope, safe_error
from ogm_agent_bridge.tools import (
    list_datasets,
)
from ogm_agent_bridge.tools import (
    query as run_query,
)
from ogm_agent_bridge.tools import (
    search_memory as run_memory_search,
)


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
    async def ogm_query(
        dataset_id: str,
        query: str,
        mode: Literal["vector_only", "graph_only", "hybrid"] | None = None,
        top_k: int | None = None,
        graph_depth: int | None = None,
        graph_fanout: int | None = None,
        graph_timeout_ms: int | None = None,
        fusion: Literal["rrf", "weighted"] | None = None,
        memory_user_id: str | None = None,
        memory_agent_id: str | None = None,
        memory_session_id: str | None = None,
        memory_top_k: int | None = None,
    ) -> dict[str, Any]:
        try:
            arguments = _defined(
                dataset_id=dataset_id,
                query=query,
                mode=mode,
                top_k=top_k,
                graph_depth=graph_depth,
                graph_fanout=graph_fanout,
                graph_timeout_ms=graph_timeout_ms,
                fusion=fusion,
                memory_user_id=memory_user_id,
                memory_agent_id=memory_agent_id,
                memory_session_id=memory_session_id,
                memory_top_k=memory_top_k,
            )
            async with OGMClient(resolved_settings) as client:
                return await run_query(client, arguments)
        except BridgeError as error:
            return safe_error(error)

    @server.tool(description="Search stored memory facts lexically.")
    async def ogm_search_memory(
        query: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
        scopes: list[Literal["user", "agent", "session"]] | None = None,
        limit: int | None = None,
        include_superseded: bool | None = None,
    ) -> dict[str, Any]:
        try:
            arguments = _defined(
                query=query,
                user_id=user_id,
                agent_id=agent_id,
                session_id=session_id,
                scopes=scopes,
                limit=limit,
                include_superseded=include_superseded,
            )
            async with OGMClient(resolved_settings) as client:
                return await run_memory_search(client, arguments)
        except BridgeError as error:
            return safe_error(error)

    @server.tool(
        description="Provision stable user and agent identities then create session."
    )
    async def ogm_create_session(
        user_external_id: str, agent_name: str, title: str | None = None
    ) -> dict[str, Any]:
        try:
            from ogm_agent_bridge.state import StateStore
            from ogm_agent_bridge.write_tools import create_session

            state = StateStore(resolved_settings.state_db, resolved_settings.project_id)
            try:
                async with OGMClient(resolved_settings) as client:
                    return await create_session(
                        client,
                        state,
                        resolved_settings.permission_profile,
                        _defined(
                            user_external_id=user_external_id,
                            agent_name=agent_name,
                            title=title,
                        ),
                    )
            finally:
                state.close()
        except BridgeError as error:
            return safe_error(error)

    @server.tool(description="Store one message and one fact in mapped active session.")
    async def ogm_remember(
        session_id: str,
        content: str,
        subject: str,
        predicate: str,
        value: str,
        role: Literal["system", "user", "assistant", "tool"] = "user",
    ) -> dict[str, Any]:
        try:
            from ogm_agent_bridge.state import StateStore
            from ogm_agent_bridge.write_tools import remember

            state = StateStore(resolved_settings.state_db, resolved_settings.project_id)
            try:
                async with OGMClient(resolved_settings) as client:
                    return await remember(
                        client,
                        state,
                        resolved_settings.permission_profile,
                        {
                            "session_id": session_id,
                            "content": content,
                            "subject": subject,
                            "predicate": predicate,
                            "value": value,
                            "role": role,
                        },
                    )
            finally:
                state.close()
        except BridgeError as error:
            return safe_error(error)

    @server.tool(description="Upload regular local file as multipart document.")
    async def ogm_upload_document(
        dataset_id: str,
        path: str,
        filename: str | None = None,
        mime_type: str | None = None,
    ) -> dict[str, Any]:
        try:
            from ogm_agent_bridge.write_tools import upload_document

            async with OGMClient(resolved_settings) as client:
                return await upload_document(
                    client,
                    resolved_settings.permission_profile,
                    dataset_id,
                    path,
                    filename,
                    mime_type,
                )
        except BridgeError as error:
            return safe_error(error)

    return server


def _defined(**values: Any) -> dict[str, Any]:
    """Drop unset optional MCP arguments before core payload validation."""
    return {name: value for name, value in values.items() if value is not None}


def main() -> None:
    """Run MCP stdio server."""
    create_server().run(transport="stdio")
