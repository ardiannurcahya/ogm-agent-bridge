import json
import os
import sqlite3
from pathlib import Path

import httpx
import pytest

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.config import Settings
from ogm_agent_bridge.errors import PermissionError, UpstreamError, ValidationError
from ogm_agent_bridge.state import StateStore
from ogm_agent_bridge.write_tools import create_session, remember, upload_document


@pytest.fixture
def settings() -> Settings:
    return Settings("https://core.test", "key", "project", 2, 1)


@pytest.mark.asyncio
async def test_create_session_payload_reuse_and_no_write_retry(
    tmp_path: Path, settings: Settings
) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.url.path, json.loads(request.content)))
        return httpx.Response(201, json={"id": f"id-{len(calls)}"})

    state = StateStore(tmp_path / "state.sqlite3", "project")
    arguments = {
        "user_external_id": "user",
        "agent_name": "agent",
        "user_display_name": "User",
        "agent_description": "Agent",
        "user_metadata": {"u": 1},
        "agent_metadata": {"a": 2},
        "title": "Title",
        "session_metadata": {"s": 3},
    }
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = OGMClient(settings, http_client)
        first = await create_session(client, state, "personal-safe", arguments)
        second = await create_session(client, state, "personal-safe", arguments)
    state.close()

    assert first["data"] == {
        "session_id": first["data"]["session_id"],
        "core_session_id": "id-3",
        "user_id": "id-1",
        "agent_id": "id-2",
    }
    assert second["data"] == {
        "session_id": first["data"]["session_id"],
        "core_session_id": "id-3",
    }
    assert calls == [
        (
            "/v1/memory/users",
            {"external_id": "user", "display_name": "User", "metadata": {"u": 1}},
        ),
        (
            "/v1/memory/agents",
            {"name": "agent", "description": "Agent", "metadata": {"a": 2}},
        ),
        (
            "/v1/memory/sessions",
            {
                "user_id": "id-1",
                "agent_id": "id-2",
                "title": "Title",
                "metadata": {"s": 3},
            },
        ),
    ]


@pytest.mark.asyncio
async def test_create_session_failure_marks_uncertain_and_never_retries(
    tmp_path: Path, settings: Settings
) -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 3:
            return httpx.Response(503)
        return httpx.Response(201, json={"id": str(calls)})

    state = StateStore(tmp_path / "state.sqlite3", "project")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(ValidationError, match="uncertain"):
            await create_session(
                OGMClient(settings, http_client),
                state,
                "personal-safe",
                {"user_external_id": "u", "agent_name": "a"},
            )
        with pytest.raises(ValidationError, match="uncertain"):
            await create_session(
                OGMClient(settings, http_client),
                state,
                "personal-safe",
                {"user_external_id": "u", "agent_name": "a"},
            )
    assert calls == 3
    state.close()


@pytest.mark.asyncio
async def test_remember_exact_payload_no_retry_and_permissions(
    tmp_path: Path, settings: Settings
) -> None:
    state = StateStore(tmp_path / "state.sqlite3", "project")
    bridge_id = state.begin_session("u", "a")
    state.finish_session(bridge_id, "core")
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.url.path == "/v1/memory/sessions/core/messages"
        assert json.loads(request.content) == {
            "messages": [
                {"role": "assistant", "content": "hello", "metadata": {"m": 1}}
            ],
            "facts": [
                {
                    "scope": "session",
                    "subject": "s",
                    "predicate": "p",
                    "value": "v",
                    "confidence": 42,
                    "metadata": {"f": 2},
                }
            ],
        }
        return httpx.Response(503)

    arguments = {
        "session_id": bridge_id,
        "message": {"role": "assistant", "content": "hello", "metadata": {"m": 1}},
        "fact": {
            "scope": "session",
            "subject": "s",
            "predicate": "p",
            "value": "v",
            "confidence": 42,
            "metadata": {"f": 2},
        },
    }
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(UpstreamError):
            await remember(
                OGMClient(settings, http_client), state, "personal-safe", arguments
            )
    assert calls == 1
    with pytest.raises(PermissionError):
        await remember(OGMClient(settings), state, "read-only", arguments)
    state.close()


def test_state_migration_permissions_restart_and_uncertain(tmp_path: Path) -> None:
    path = tmp_path / "private" / "state.sqlite3"
    state = StateStore(path, "project")
    assert os.stat(path).st_mode & 0o777 == 0o600
    assert state.db.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    state.begin_identity("users", "u")
    state.begin_session("u", "a")
    state.close()
    restarted = StateStore(path, "project")
    assert restarted.identity("users", "u") == (None, "uncertain")
    session = restarted.session("u", "a")
    assert session is not None
    assert session[2] == "uncertain"
    restarted.close()
    assert sqlite3.connect(path).execute(
        "SELECT version FROM schema_version"
    ).fetchone() == (1,)


@pytest.mark.asyncio
async def test_upload_regular_file_validation_and_multipart(
    tmp_path: Path, settings: Settings
) -> None:
    source = tmp_path / "document.txt"
    source.write_text("hello")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["content-type"].startswith("multipart/form-data;")
        assert b'name="file"; filename="named.txt"' in request.content
        assert b"hello" in request.content
        return httpx.Response(201, json={"id": "doc"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        result = await upload_document(
            OGMClient(settings, http_client),
            "personal-safe",
            "dataset",
            str(source),
            "named.txt",
            "text/plain",
        )
    assert result["data"] == {"id": "doc"}
    with pytest.raises(ValidationError):
        await upload_document(
            OGMClient(settings), "personal-safe", "dataset", str(tmp_path), None, None
        )
    with pytest.raises(PermissionError):
        await upload_document(
            OGMClient(settings), "read-only", "dataset", str(source), None, None
        )
