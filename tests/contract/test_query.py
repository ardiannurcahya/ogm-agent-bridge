import json

import httpx
import pytest

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.config import Settings
from ogm_agent_bridge.errors import ValidationError
from ogm_agent_bridge.tools import query


@pytest.mark.asyncio
async def test_query_preserves_core_fields() -> None:
    core = {
        "answer": "answer",
        "citations": [{"text": "exact"}],
        "retrieval_trace": {"trace_id": "trace"},
        "usage": {"total_tokens": 2},
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content) == {
            "dataset_id": "dataset",
            "query": "question",
            "top_k": 2,
        }
        return httpx.Response(200, json=core)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        result = await query(
            OGMClient(Settings("https://core.test", "key", "project"), http_client),
            {"dataset_id": "dataset", "query": "question", "top_k": 2},
        )

    assert result["data"] == core
    assert result["provenance"] == {
        "project_id": "project",
        "dataset_id": "dataset",
        "trace_id": "trace",
    }


@pytest.mark.asyncio
async def test_query_rejects_core_invalid_input() -> None:
    with pytest.raises(ValidationError):
        await query(
            OGMClient(Settings("https://core.test", "key", "project")),
            {"dataset_id": "", "query": "q"},
        )
