import json

import httpx
import pytest

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.config import Settings
from ogm_agent_bridge.errors import ValidationError
from ogm_agent_bridge.tools import search_memory


@pytest.mark.asyncio
async def test_memory_search_warns_lexical() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/memory/search"
        assert json.loads(request.content) == {"query": "preference", "limit": 5}
        return httpx.Response(
            200, json=[{"id": "fact", "matched_terms": ["preference"]}]
        )

    settings = Settings("https://core.test", "key", "project")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        result = await search_memory(
            OGMClient(settings, http_client), {"query": "preference", "limit": 5}
        )

    assert result["warnings"] == ["Memory search is lexical, not semantic retrieval."]
    assert result["provenance"] == {"project_id": "project"}


@pytest.mark.asyncio
async def test_memory_search_validates_scope() -> None:
    with pytest.raises(ValidationError):
        await search_memory(
            OGMClient(Settings("https://core.test", "key", "project")),
            {"query": "memory", "scopes": ["bad"]},
        )
