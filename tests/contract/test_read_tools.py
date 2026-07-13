import httpx
import pytest

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.config import Settings
from ogm_agent_bridge.tools import list_datasets


@pytest.mark.asyncio
async def test_list_datasets_sends_project_auth_and_envelope() -> None:
    settings = Settings("https://core.example.test", "api-key", "project-id")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/datasets"
        assert request.headers["X-API-Key"] == "api-key"
        assert request.headers["X-Project-Id"] == "project-id"
        return httpx.Response(200, json=[{"id": "dataset-1", "name": "Docs"}])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        result = await list_datasets(OGMClient(settings, http_client))

    assert result == {
        "ok": True,
        "data": [{"id": "dataset-1", "name": "Docs"}],
        "provenance": {"project_id": "project-id"},
        "warnings": [],
    }
