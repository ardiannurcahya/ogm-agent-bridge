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
        "ogm_search_entities",
        "ogm_get_entity",
        "ogm_get_neighbors",
        "ogm_find_path",
        "ogm_get_subgraph",
        "ogm_get_graph",
        "ogm_get_evidence",
        "ogm_get_relation_evidence",
        "ogm_upload_document",
        "ogm_memory_list_episodes",
        "ogm_memory_get_episode",
        "ogm_memory_search",
        "ogm_memory_create_episode",
        "ogm_memory_append_attempt",
        "ogm_memory_record_outcome",
        "ogm_memory_feedback_episode",
        "ogm_memory_supersede_episode",
        "ogm_memory_feedback_pattern",
        "ogm_memory_supersede_pattern",
    }
    assert tools["ogm_search_entities"]["required"] == ["dataset_id", "q"]
    assert tools["ogm_find_path"]["required"] == [
        "dataset_id",
        "source_entity_id",
        "target_entity_id",
    ]
    assert tools["ogm_get_subgraph"]["required"] == ["dataset_id", "entity_id"]
    assert tools["ogm_get_relation_evidence"]["required"] == [
        "dataset_id",
        "relation_id",
    ]
    upload = tools["ogm_upload_document"]
    assert upload["required"] == ["dataset_id", "path"]
    assert upload["properties"]["path"]["type"] == "string"
    assert tools["ogm_memory_search"]["required"] == ["q"]
    assert tools["ogm_memory_create_episode"]["required"] == [
        "domain",
        "title",
        "goal",
        "problem_signature",
    ]
    assert tools["ogm_memory_append_attempt"]["required"] == [
        "episode_id",
        "hypothesis",
        "result",
    ]
