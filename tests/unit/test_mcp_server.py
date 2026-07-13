import httpx
import pytest

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.config import Settings
from ogm_agent_bridge.mcp_server import create_server, health


@pytest.mark.asyncio
async def test_health_uses_no_project_headers() -> None:
    settings = Settings("https://core.example.test", "api-key", "project-id")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/health"
        assert "X-API-Key" not in request.headers
        assert "X-Project-Id" not in request.headers
        return httpx.Response(200, json={"status": "ok"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        result = await health(OGMClient(settings, http_client))

    assert result == {
        "ok": True,
        "data": {"status": "ok"},
        "provenance": {},
        "warnings": [],
    }


def test_server_registers_health_tool() -> None:
    server = create_server(Settings("https://core.example.test", "key", "project"))

    assert "ogm_health" in server._tool_manager._tools


@pytest.mark.asyncio
async def test_server_exposes_explicit_read_tool_schemas() -> None:
    server = create_server(Settings("https://core.example.test", "key", "project"))
    tools = {tool.name: tool.inputSchema for tool in await server.list_tools()}

    assert set(tools) == {
        "ogm_health",
        "ogm_list_datasets",
        "ogm_query",
        "ogm_search_memory",
        "ogm_create_session",
        "ogm_remember",
        "ogm_upload_document",
    }
    assert "memory_session_id" in tools["ogm_query"]["properties"]
    assert "graph_timeout_ms" in tools["ogm_query"]["properties"]
    assert "session_id" in tools["ogm_search_memory"]["properties"]
    assert "include_superseded" in tools["ogm_search_memory"]["properties"]
    assert "options" not in tools["ogm_query"]["properties"]
    create = tools["ogm_create_session"]
    assert create["required"] == ["user_external_id", "agent_name"]
    assert set(create["properties"]) >= {
        "user_display_name",
        "agent_description",
        "user_metadata",
        "agent_metadata",
        "session_metadata",
    }
    remember = tools["ogm_remember"]
    assert remember["required"] == ["session_id", "message", "fact"]
    assert remember["properties"]["message"]["type"] == "object"
    assert remember["properties"]["fact"]["type"] == "object"
    upload = tools["ogm_upload_document"]
    assert upload["required"] == ["dataset_id", "path"]
    assert upload["properties"]["path"]["type"] == "string"
