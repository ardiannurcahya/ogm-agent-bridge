import httpx
import pytest

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.config import Settings
from ogm_agent_bridge.errors import ValidationError
from ogm_agent_bridge.tools import (
    get_graph,
    get_relation_evidence,
    list_datasets,
)


@pytest.fixture
def settings() -> Settings:
    return Settings("https://core.example.test", "api-key", "project-id")


@pytest.mark.asyncio
async def test_list_datasets_sends_project_auth_and_envelope(
    settings: Settings,
) -> None:
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


@pytest.mark.asyncio
async def test_graph_reads_use_exact_paths_params_and_preserve_response(
    settings: Settings,
) -> None:
    responses = [{"nodes": [{"id": "n"}]}, [{"id": "evidence"}]]
    calls: list[tuple[str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.url.path, request.url.query.decode()))
        return httpx.Response(200, json=responses[len(calls) - 1])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = OGMClient(settings, http_client)
        graph = await get_graph(
            client,
            {
                "dataset_id": "dataset",
                "limit": 200,
                "depth": 1,
            },
        )
        evidence = await get_relation_evidence(
            client, {"dataset_id": "dataset", "relation_id": "relation", "limit": 1}
        )

    assert calls == [
        (
            "/v1/datasets/dataset/graph",
            "limit=200&depth=1",
        ),
        ("/v1/datasets/dataset/relations/relation/evidence", "limit=1"),
    ]
    assert graph["data"] == responses[0]
    assert evidence["data"] == responses[1]
    assert evidence["provenance"] == {
        "project_id": "project-id",
        "dataset_id": "dataset",
        "relation_id": "relation",
    }


@pytest.mark.asyncio
async def test_graph_read_validation(settings: Settings) -> None:
    client = OGMClient(settings)
    with pytest.raises(ValidationError):
        await get_graph(client, {"dataset_id": "", "limit": 1})
    with pytest.raises(ValidationError):
        await get_graph(client, {"dataset_id": "dataset", "limit": 201})
    with pytest.raises(ValidationError):
        await get_graph(client, {"dataset_id": "dataset", "depth": 2})
    with pytest.raises(ValidationError):
        await get_relation_evidence(
            client, {"dataset_id": "dataset", "relation_id": "", "limit": 1}
        )
    await client.aclose()
