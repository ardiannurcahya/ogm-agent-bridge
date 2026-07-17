"""Optional real-core smoke test. Never starts Docker or reads credentials."""

from __future__ import annotations

import os

import httpx
import pytest

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.config import load_settings
from ogm_agent_bridge.tools import list_datasets, search_entities

pytestmark = pytest.mark.skipif(
    os.environ.get("OGM_REAL_CORE_SMOKE") != "1",
    reason="set OGM_REAL_CORE_SMOKE=1 with isolated real-core environment",
)


@pytest.mark.asyncio
async def test_real_core_health_requires_explicit_isolated_environment() -> None:
    required = ("OGM_BASE_URL", "OGM_API_KEY", "OGM_PROJECT_ID")
    assert all(os.environ.get(name) for name in required)
    settings = load_settings()
    async with OGMClient(settings) as client:
        response = await client.request("GET", "/health", authenticated=False)
    assert response.status_code == httpx.codes.OK


@pytest.mark.asyncio
async def test_real_core_graph_search_when_dataset_is_configured() -> None:
    dataset_id = os.environ.get("OGM_REAL_CORE_DATASET_ID")
    if not dataset_id:
        pytest.skip("set OGM_REAL_CORE_DATASET_ID to run graph search smoke")
    settings = load_settings()
    async with OGMClient(settings) as client:
        datasets = await list_datasets(client)
        assert any(item.get("id") == dataset_id for item in datasets["data"])
        result = await search_entities(
            client, {"dataset_id": dataset_id, "q": "a", "limit": 1}
        )
    assert result["ok"] is True
    assert result["provenance"]["dataset_id"] == dataset_id
