import httpx
import pytest

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.config import Settings
from ogm_agent_bridge.errors import ValidationError
from ogm_agent_bridge.tools import (
    get_community_report,
    graph_explorer,
    list_community_report_jobs,
    list_community_reports,
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
    responses = [{"nodes": [{"id": "n"}]}, [{"id": "r"}], {"id": "r1"}, [{"id": "j"}]]
    calls: list[tuple[str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.url.path, request.url.query.decode()))
        return httpx.Response(200, json=responses[len(calls) - 1])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = OGMClient(settings, http_client)
        explorer = await graph_explorer(
            client,
            {
                "dataset_id": "dataset",
                "node_limit": 200,
                "relation_limit": 1,
                "community_level": 2,
            },
        )
        reports = await list_community_reports(
            client, {"dataset_id": "dataset", "community_level": 0}
        )
        report = await get_community_report(
            client, {"dataset_id": "dataset", "report_id": "report"}
        )
        jobs = await list_community_report_jobs(client, {"dataset_id": "dataset"})

    assert calls == [
        (
            "/v1/datasets/dataset/graph/explorer",
            "node_limit=200&relation_limit=1&community_level=2",
        ),
        ("/v1/datasets/dataset/community-reports", "community_level=0"),
        ("/v1/datasets/dataset/community-reports/report", ""),
        ("/v1/datasets/dataset/community-report-jobs", ""),
    ]
    assert explorer["data"] == responses[0]
    assert reports["data"] == responses[1]
    assert report["data"] == responses[2]
    assert jobs["data"] == responses[3]
    assert report["provenance"] == {
        "project_id": "project-id",
        "dataset_id": "dataset",
        "report_id": "report",
    }


@pytest.mark.asyncio
async def test_graph_read_validation(settings: Settings) -> None:
    client = OGMClient(settings)
    with pytest.raises(ValidationError):
        await graph_explorer(client, {"dataset_id": "", "node_limit": 1})
    with pytest.raises(ValidationError):
        await graph_explorer(client, {"dataset_id": "dataset", "relation_limit": 201})
    with pytest.raises(ValidationError):
        await list_community_reports(
            client, {"dataset_id": "dataset", "community_level": 3}
        )
    with pytest.raises(ValidationError):
        await get_community_report(client, {"dataset_id": "dataset", "report_id": ""})
    await client.aclose()
