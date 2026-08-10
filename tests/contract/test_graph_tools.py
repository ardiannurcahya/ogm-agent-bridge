import httpx
import pytest

import ogm_mcp_skills.write_tools as write_tools
from ogm_mcp_skills.client import OGMClient
from ogm_mcp_skills.config import Settings
from ogm_mcp_skills.errors import ValidationError
from ogm_mcp_skills.tools import (
    find_path,
    get_entity,
    get_evidence,
    get_graph,
    get_neighbors,
    get_relation_evidence,
    get_subgraph,
    search_entities,
)
from ogm_mcp_skills.write_tools import upload_document


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
    with pytest.raises(ValidationError):
        await search_entities(
            OGMClient(settings), {"dataset_id": "dataset/escape", "q": "q"}
        )
    with pytest.raises(ValidationError):
        await get_graph(OGMClient(settings), {"dataset_id": "dataset", "unknown": 1})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("handler", "arguments", "selector_name"),
    [
        (search_entities, {"dataset_id": "dataset", "q": "q"}, "dataset_id"),
        (get_entity, "entity", None),
        (get_neighbors, {"entity_id": "entity"}, "entity_id"),
        (
            find_path,
            {
                "dataset_id": "dataset",
                "source_entity_id": "source",
                "target_entity_id": "target",
            },
            "dataset_id",
        ),
        (
            get_subgraph,
            {"dataset_id": "dataset", "entity_id": "entity"},
            "dataset_id",
        ),
        (get_graph, {"dataset_id": "dataset"}, "dataset_id"),
        (get_evidence, "evidence", None),
        (
            get_relation_evidence,
            {"dataset_id": "dataset", "relation_id": "relation"},
            "dataset_id",
        ),
        (
            get_relation_evidence,
            {"dataset_id": "dataset", "relation_id": "relation"},
            "relation_id",
        ),
    ],
)
@pytest.mark.parametrize(
    "identifier",
    [
        "value?x=1",
        "value#fragment",
        "value%2fescape",
        "value&x=1",
        "value/escape",
        "value\\escape",
        "value\nvalue",
    ],
)
async def test_graph_tools_reject_route_delimiter_injection(
    settings, handler, arguments, selector_name, identifier
):
    if isinstance(arguments, dict):
        assert selector_name is not None
        arguments = {**arguments, selector_name: identifier}
    else:
        arguments = identifier
    with pytest.raises(ValidationError, match="safe route component"):
        await handler(OGMClient(settings), arguments)


@pytest.mark.asyncio
async def test_upload_regular_file_validation_and_multipart(tmp_path, settings):
    source = tmp_path / "document.txt"
    source.write_text("hello")
    allowed_root = tmp_path.resolve()

    async def mock(request: httpx.Request) -> httpx.Response:
        assert request.headers["content-type"].startswith("multipart/form-data;")
        assert b'name="file"; filename="named.txt"' in request.content
        return httpx.Response(201, json={"id": "doc"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock)) as http_client:
        result = await upload_document(
            OGMClient(settings, http_client),
            "personal-safe",
            "00000000-0000-0000-0000-000000000002",
            source.name,
            "named.txt",
            "text/plain",
            (allowed_root,),
        )
    assert result["data"] == {"id": "doc"}
    with pytest.raises(ValidationError):
        await upload_document(
            OGMClient(settings),
            "personal-safe",
            "invalid",
            source.name,
            None,
            None,
            (tmp_path.resolve(),),
        )


@pytest.mark.asyncio
async def test_upload_rejects_absent_upload_roots_before_file_open_or_request(
    settings, monkeypatch
):
    def fail_open(*args, **kwargs):
        raise AssertionError("os.open must not be called without upload roots")

    async def mock(request: httpx.Request) -> httpx.Response:
        raise AssertionError("request must not be sent without upload roots")

    monkeypatch.setattr(write_tools.os, "open", fail_open)
    async with httpx.AsyncClient(transport=httpx.MockTransport(mock)) as http_client:
        with pytest.raises(ValidationError, match="upload roots"):
            await upload_document(
                OGMClient(settings, http_client),
                "personal-safe",
                "00000000-0000-0000-0000-000000000002",
                "document.txt",
                "document.txt",
                None,
                (),
            )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "filename",
    [
        "nested/name.txt",
        "nested\\name.txt",
        "line\nbreak.txt",
        "nul\x00byte.txt",
        "x" * 256,
    ],
)
async def test_upload_rejects_non_basename_or_unbounded_filename(
    tmp_path, settings, filename
):
    source = tmp_path / "document.txt"
    source.write_text("hello")

    with pytest.raises(ValidationError, match="bounded basename"):
        await upload_document(
            OGMClient(settings),
            "personal-safe",
            "00000000-0000-0000-0000-000000000002",
            source.name,
            filename,
            None,
            (tmp_path.resolve(),),
        )


@pytest.mark.asyncio
async def test_upload_rejects_control_character_in_derived_source_filename(
    tmp_path, settings
):
    source = tmp_path / "line\nbreak.txt"
    source.write_text("hello")

    with pytest.raises(ValidationError, match="bounded basename"):
        await upload_document(
            OGMClient(settings),
            "personal-safe",
            "00000000-0000-0000-0000-000000000002",
            source.name,
            None,
            None,
            (tmp_path.resolve(),),
        )


@pytest.mark.asyncio
async def test_upload_accepts_bounded_basename(tmp_path, settings):
    source = tmp_path / "document.txt"
    source.write_text("hello")

    async def mock(request: httpx.Request) -> httpx.Response:
        return httpx.Response(201, json={"id": "doc"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock)) as http_client:
        await upload_document(
            OGMClient(settings, http_client),
            "personal-safe",
            "00000000-0000-0000-0000-000000000002",
            source.name,
            "x" * 255,
            None,
            (tmp_path.resolve(),),
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mime_type",
    [
        "",
        "text",
        "text/",
        "/plain",
        "text/plain\r\nX-Injected: yes",
        "text/\x00plain",
        "x" * 256,
        1,
        False,
    ],
)
async def test_upload_rejects_malformed_or_oversized_mime_type(
    tmp_path, settings, mime_type
):
    source = tmp_path / "document.txt"
    source.write_text("hello")

    with pytest.raises(ValidationError, match="bounded media type"):
        await upload_document(
            OGMClient(settings),
            "personal-safe",
            "00000000-0000-0000-0000-000000000002",
            source.name,
            None,
            mime_type,
            (tmp_path.resolve(),),
        )


@pytest.mark.asyncio
async def test_upload_rejects_oversized_path_before_resolution(tmp_path, settings):
    with pytest.raises(ValidationError, match="bounded non-empty string"):
        await upload_document(
            OGMClient(settings),
            "personal-safe",
            "00000000-0000-0000-0000-000000000002",
            "x" * 4_097,
            None,
            None,
            (tmp_path.resolve(),),
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mime_type",
    [
        "application/json",
        "application/vnd.ogm.document+json",
        "application/" + "x" * 243,
    ],
)
async def test_upload_accepts_mime_type_grammar_boundaries(
    tmp_path, settings, mime_type
):
    source = tmp_path / "document.txt"
    source.write_text("hello")

    async def mock(request: httpx.Request) -> httpx.Response:
        return httpx.Response(201, json={"id": "doc"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock)) as http_client:
        await upload_document(
            OGMClient(settings, http_client),
            "personal-safe",
            "00000000-0000-0000-0000-000000000002",
            source.name,
            None,
            mime_type,
            (tmp_path.resolve(),),
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["embedded\x00nul", "x" * 4_096])
async def test_upload_normalizes_nul_and_boundary_path_failures(
    tmp_path, settings, path
):
    with pytest.raises(ValidationError, match="path must name a regular file"):
        await upload_document(
            OGMClient(settings),
            "personal-safe",
            "00000000-0000-0000-0000-000000000002",
            path,
            None,
            None,
            (tmp_path.resolve(),),
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("target", "error"),
    [
        ("open", ValueError("invalid path")),
        ("open", OSError("unavailable")),
        ("open", RuntimeError("invalid path state")),
    ],
)
async def test_upload_normalizes_path_handling_exceptions(
    tmp_path, settings, monkeypatch, target, error
):
    source = tmp_path / "document.txt"
    source.write_text("hello")
    allowed_root = tmp_path.resolve()

    if target == "open":

        def fail_open(*args, **kwargs):
            raise error

        monkeypatch.setattr(write_tools.os, "open", fail_open)

    with pytest.raises(ValidationError, match="path must name a regular file"):
        await upload_document(
            OGMClient(settings),
            "personal-safe",
            "00000000-0000-0000-0000-000000000002",
            source.name,
            None,
            None,
            (allowed_root,),
        )


@pytest.mark.asyncio
async def test_upload_accepts_absolute_path_below_approved_root(tmp_path, settings):
    source = tmp_path / "document.txt"
    source.write_text("hello")

    async def mock(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith(
            "/v1/datasets/00000000-0000-0000-0000-000000000002/documents"
        )
        return httpx.Response(201, json={"id": "doc"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock)) as http_client:
        result = await upload_document(
            OGMClient(settings, http_client),
            "personal-safe",
            "00000000-0000-0000-0000-000000000002",
            str(source),
            None,
            None,
            (tmp_path,),
        )

    assert result["data"] == {"id": "doc"}


@pytest.mark.asyncio
async def test_upload_rejects_parent_symlink_and_closes_directory_fd(
    tmp_path, settings, monkeypatch
):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "document.txt").write_text("secret")
    (tmp_path / "linked").symlink_to(outside, target_is_directory=True)
    closed_fds: list[int] = []
    original_close = write_tools.os.close

    def record_close(fd: int) -> None:
        closed_fds.append(fd)
        original_close(fd)

    monkeypatch.setattr(write_tools.os, "close", record_close)
    with pytest.raises(ValidationError, match="path must name a regular file"):
        await upload_document(
            OGMClient(settings),
            "personal-safe",
            "00000000-0000-0000-0000-000000000002",
            "linked/document.txt",
            None,
            None,
            (tmp_path,),
        )
    assert closed_fds


@pytest.mark.asyncio
async def test_upload_rejects_directory_and_closes_its_fd(
    tmp_path, settings, monkeypatch
):
    directory = tmp_path / "directory"
    directory.mkdir()
    closed_fds: list[int] = []
    original_close = write_tools.os.close

    def record_close(fd: int) -> None:
        closed_fds.append(fd)
        original_close(fd)

    monkeypatch.setattr(write_tools.os, "close", record_close)
    with pytest.raises(ValidationError, match="path must name a regular file"):
        await upload_document(
            OGMClient(settings),
            "personal-safe",
            "00000000-0000-0000-0000-000000000002",
            "directory",
            None,
            None,
            (tmp_path,),
        )
    assert len(closed_fds) >= 2
