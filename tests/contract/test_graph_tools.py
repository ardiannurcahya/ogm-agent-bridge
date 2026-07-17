import httpx
import pytest

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.config import Settings
from ogm_agent_bridge.errors import ValidationError
from ogm_agent_bridge.tools import (
    find_path,
    get_evidence,
    get_graph,
    get_neighbors,
    get_relation_evidence,
    get_subgraph,
    search_entities,
)
from ogm_agent_bridge.write_tools import upload_document


@pytest.fixture
def settings() -> Settings:
    return Settings("https://core.test", "key", "project")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("handler", "arguments", "path", "params", "provenance"),
    [
        (
            search_entities,
            {"dataset_id": "dataset", "q": "Python", "limit": 2},
            "/v1/datasets/dataset/entities/search",
            {"q": "Python", "limit": "2"},
            {"project_id": "project", "dataset_id": "dataset"},
        ),
        (
            get_neighbors,
            {"entity_id": "entity", "limit": 2},
            "/v1/entities/entity/neighbors",
            {"limit": "2"},
            {"project_id": "project", "entity_id": "entity"},
        ),
        (
            find_path,
            {
                "dataset_id": "dataset",
                "source_entity_id": "source",
                "target_entity_id": "target",
                "max_depth": 2,
            },
            "/v1/datasets/dataset/graph/path",
            {
                "source_entity_id": "source",
                "target_entity_id": "target",
                "max_depth": "2",
            },
            {"project_id": "project", "dataset_id": "dataset"},
        ),
        (
            get_subgraph,
            {"dataset_id": "dataset", "entity_id": "entity", "depth": 2},
            "/v1/datasets/dataset/graph/subgraph",
            {"entity_id": "entity", "depth": "2"},
            {"project_id": "project", "dataset_id": "dataset"},
        ),
        (
            get_graph,
            {"dataset_id": "dataset", "limit": 2, "depth": 1},
            "/v1/datasets/dataset/graph",
            {"limit": "2", "depth": "1"},
            {"project_id": "project", "dataset_id": "dataset"},
        ),
        (
            get_relation_evidence,
            {"dataset_id": "dataset", "relation_id": "relation", "limit": 2},
            "/v1/datasets/dataset/relations/relation/evidence",
            {"limit": "2"},
            {
                "project_id": "project",
                "dataset_id": "dataset",
                "relation_id": "relation",
            },
        ),
    ],
)
async def test_graph_tools_call_current_core_routes(
    handler, arguments, path, params, provenance, settings
):
    async def mock(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == path
        assert dict(request.url.params) == params
        assert request.headers["X-API-Key"] == "key"
        assert request.headers["X-Project-Id"] == "project"
        return httpx.Response(200, json={"result": True})

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock)) as http_client:
        result = await handler(OGMClient(settings, http_client), arguments)
    assert result["data"] == {"result": True}
    assert result["provenance"] == provenance


@pytest.mark.asyncio
async def test_evidence_calls_current_core_route(settings):
    async def mock(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/evidence/evidence"
        return httpx.Response(200, json={"id": "evidence"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock)) as http_client:
        result = await get_evidence(OGMClient(settings, http_client), "evidence")
    assert result["provenance"] == {"project_id": "project", "evidence_id": "evidence"}


@pytest.mark.asyncio
async def test_graph_tools_reject_core_limit_violations(settings):
    with pytest.raises(ValidationError):
        await search_entities(
            OGMClient(settings), {"dataset_id": "dataset", "q": "q", "limit": 101}
        )
    with pytest.raises(ValidationError):
        await get_subgraph(
            OGMClient(settings),
            {"dataset_id": "dataset", "entity_id": "entity", "depth": 3},
        )


@pytest.mark.asyncio
async def test_upload_regular_file_validation_and_multipart(tmp_path, settings):
    source = tmp_path / "document.txt"
    source.write_text("hello")

    async def mock(request: httpx.Request) -> httpx.Response:
        assert request.headers["content-type"].startswith("multipart/form-data;")
        assert b'name="file"; filename="named.txt"' in request.content
        return httpx.Response(201, json={"id": "doc"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock)) as http_client:
        result = await upload_document(
            OGMClient(settings, http_client),
            "personal-safe",
            "00000000-0000-0000-0000-000000000002",
            str(source),
            "named.txt",
            "text/plain",
            (tmp_path.resolve(),),
        )
    assert result["data"] == {"id": "doc"}
    with pytest.raises(ValidationError):
        await upload_document(
            OGMClient(settings),
            "personal-safe",
            "invalid",
            str(source),
            None,
            None,
            (tmp_path.resolve(),),
        )
