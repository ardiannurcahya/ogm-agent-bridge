"""B4 lightweight bridge conformance checks; no real core required."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.config import Settings
from ogm_agent_bridge.errors import (
    AuthenticationError,
    NotFoundError,
    PayloadTooLargeError,
    PermissionError,
    UnsupportedMediaError,
    UpstreamError,
    ValidationError,
)
from ogm_agent_bridge.mcp_server import _tool_error, create_server
from ogm_agent_bridge.tools import query, search_memory
from ogm_agent_bridge.write_tools import upload_document


@pytest.fixture
def settings() -> Settings:
    return Settings("https://core.test", "key", "project")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "error"),
    [
        (400, ValidationError),
        (401, AuthenticationError),
        (403, PermissionError),
        (404, NotFoundError),
        (413, PayloadTooLargeError),
        (415, UnsupportedMediaError),
        (422, ValidationError),
        (500, UpstreamError),
    ],
)
async def test_http_error_matrix_closes_response(
    settings: Settings, status: int, error: type[Exception]
) -> None:
    response: httpx.Response | None = None

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal response
        response = httpx.Response(status, json={"detail": "failure"})
        return response

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(error, match="failure"):
            await OGMClient(settings, http_client).request("GET", "/v1/test")

    assert response is not None and response.is_closed


@pytest.mark.asyncio
async def test_retry_and_no_retry_counts(settings: Settings) -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503 if calls < 3 else 200)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        assert (
            await OGMClient(settings, http_client).request("GET", "/v1/test")
        ).status_code == 200
    assert calls == 3

    calls = 0
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(UpstreamError):
            await OGMClient(settings, http_client).request(
                "POST", "/v1/test", retry=False
            )
    assert calls == 1


@pytest.mark.asyncio
async def test_deep_query_response_and_memory_defaults_preserved(
    settings: Settings,
) -> None:
    core = {
        "answer": {"nested": [{"citations": [{"id": "c1"}]}]},
        "extra": [1, {"x": True}],
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        if request.url.path == "/v1/query":
            assert payload == {"dataset_id": "dataset", "query": "q"}
            return httpx.Response(200, json=core)
        assert payload == {"query": "q"}
        return httpx.Response(200, json=[])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = OGMClient(settings, http_client)
        assert (await query(client, {"dataset_id": "dataset", "query": "q"}))[
            "data"
        ] == core
        assert (await search_memory(client, {"query": "q"}))["data"] == []


@pytest.mark.asyncio
async def test_upload_root_symlink_mime_and_errors(
    tmp_path: Path, settings: Settings
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    source = root / "note.unknown"
    source.write_text("content")
    outside = tmp_path / "outside.txt"
    outside.write_text("no")
    link = root / "link.txt"
    link.symlink_to(outside)

    async def handler(request: httpx.Request) -> httpx.Response:
        assert b"application/octet-stream" in request.content
        return httpx.Response(200, json={"id": "document"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        result = await upload_document(
            OGMClient(settings, http_client),
            "personal-safe",
            "00000000-0000-0000-0000-000000000002",
            str(source),
            None,
            None,
            (root.resolve(),),
        )
    assert result["data"] == {"id": "document"}
    for bad_path in (str(link), str(outside)):
        with pytest.raises(ValidationError):
            await upload_document(
                OGMClient(settings),
                "personal-safe",
                "00000000-0000-0000-0000-000000000002",
                bad_path,
                None,
                None,
                (root.resolve(),),
            )


@pytest.mark.asyncio
async def test_mcp_eleven_tool_schemas_and_safe_unexpected_error() -> None:
    server = create_server(Settings("https://core.test", "key", "project"))
    tools = await server.list_tools()
    assert len(tools) == 11
    assert all(tool.inputSchema.get("type") == "object" for tool in tools)
    result = _tool_error(RuntimeError("secret path /private/token"))
    assert result["ok"] is False
    assert result["error"]["message"] == "Internal bridge error"
    assert "secret" not in str(result)
