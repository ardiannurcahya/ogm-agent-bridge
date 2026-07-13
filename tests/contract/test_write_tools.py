import asyncio
import concurrent.futures
import json
import os
import sqlite3
import threading
from pathlib import Path

import httpx
import pytest

from ogm_agent_bridge import write_tools
from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.config import Settings
from ogm_agent_bridge.errors import BridgeError, PermissionError, ValidationError
from ogm_agent_bridge.state import StateStore
from ogm_agent_bridge.write_tools import create_session, remember, upload_document


@pytest.fixture
def settings() -> Settings:
    return Settings("https://core.test", "key", "project", 2, 1)


@pytest.mark.asyncio
async def test_create_session_creates_switchable_sessions_and_reuses_identities(
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
        "session_id": second["data"]["session_id"],
        "core_session_id": "id-4",
        "user_id": "id-1",
        "agent_id": "id-2",
    }
    assert second["data"]["session_id"] != first["data"]["session_id"]
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
        with pytest.raises(BridgeError, match="session blocked"):
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
    bridge_id = state.begin_session("u", "a")
    state.close()
    restarted = StateStore(path, "project")
    assert restarted.identity("users", "u") == (None, "uncertain")
    assert restarted.resolve_session(bridge_id) is None
    restarted.close()
    assert sqlite3.connect(path).execute(
        "SELECT version FROM schema_version"
    ).fetchone() == (3,)


def test_v1_migration_retains_sessions_and_allows_duplicate_identity(
    tmp_path: Path,
) -> None:
    path = tmp_path / "state.sqlite3"
    db = sqlite3.connect(path)
    db.executescript("""
    CREATE TABLE schema_version (version INTEGER NOT NULL);
    INSERT INTO schema_version VALUES (1);
    CREATE TABLE users (project_id TEXT NOT NULL, external_id TEXT NOT NULL, core_id TEXT, status TEXT NOT NULL CHECK(status IN ('provisioning','active','uncertain')), PRIMARY KEY(project_id, external_id));
    CREATE TABLE agents (project_id TEXT NOT NULL, name TEXT NOT NULL, core_id TEXT, status TEXT NOT NULL CHECK(status IN ('provisioning','active','uncertain')), PRIMARY KEY(project_id, name));
    CREATE TABLE sessions (project_id TEXT NOT NULL, bridge_id TEXT NOT NULL, user_external_id TEXT NOT NULL, agent_name TEXT NOT NULL, core_id TEXT, status TEXT NOT NULL CHECK(status IN ('provisioning','active','uncertain')), PRIMARY KEY(project_id, bridge_id), UNIQUE(project_id, user_external_id, agent_name));
    INSERT INTO users VALUES ('project', 'user', 'core-user', 'active');
    INSERT INTO agents VALUES ('project', 'agent', 'core-agent', 'active');
    INSERT INTO sessions VALUES ('project', 'old', 'user', 'agent', 'core-old', 'active');
    """)
    db.close()

    state = StateStore(path, "project")
    new_bridge_id = state.begin_session("user", "agent")

    assert new_bridge_id != "old"
    assert state.resolve_session("old") == "core-old"
    assert state.identity("users", "user") == ("core-user", "active")
    assert state.identity("agents", "agent") == ("core-agent", "active")
    assert state.db.execute("SELECT COUNT(*) FROM sessions").fetchone() == (2,)
    assert state.db.execute("SELECT version FROM schema_version").fetchone() == (3,)
    state.close()


def test_identity_claim_is_atomic_across_connections(tmp_path: Path) -> None:
    path = tmp_path / "state.sqlite3"
    StateStore(path, "project").close()
    ready = threading.Barrier(2)

    def claim() -> tuple[str | None, str]:
        state = StateStore(path, "project")
        ready.wait()
        result = state.begin_identity("users", "user")
        state.close()
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: claim(), range(2)))
    assert sorted(results, key=lambda result: result[1]) == [
        (None, "claimed"),
        (None, "provisioning"),
    ]


@pytest.mark.asyncio
async def test_concurrent_session_creation_posts_each_identity_once(
    tmp_path: Path, settings: Settings
) -> None:
    calls: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        await asyncio.sleep(0.01)
        return httpx.Response(201, json={"id": request.url.path.rsplit("/", 1)[-1]})

    arguments = {"user_external_id": "user", "agent_name": "agent"}
    first = StateStore(tmp_path / "state.sqlite3", "project")
    second = StateStore(tmp_path / "state.sqlite3", "project")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        results = await asyncio.gather(
            create_session(
                OGMClient(settings, http_client), first, "personal-safe", arguments
            ),
            create_session(
                OGMClient(settings, http_client), second, "personal-safe", arguments
            ),
            return_exceptions=True,
        )
    first.close()
    second.close()

    assert calls.count("/v1/memory/users") == 1
    assert calls.count("/v1/memory/agents") == 1
    assert sum(isinstance(result, ValidationError) for result in results) == 1


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
            "00000000-0000-0000-0000-000000000002",
            str(tmp_path),
            None,
            None,
        )
    with pytest.raises(PermissionError):
        await upload_document(
            OGMClient(settings),
            "read-only",
            "00000000-0000-0000-0000-000000000002",
            str(source),
            None,
            None,
        )


@pytest.mark.asyncio
async def test_upload_rejects_symlink_swapped_after_containment(
    tmp_path: Path, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "document.txt"
    source.write_text("safe")
    secret = tmp_path / "secret.txt"
    secret.write_text("secret")
    original_open = os.open

    def swap_then_open(path: os.PathLike[str], flags: int, *args: int) -> int:
        source.unlink()
        source.symlink_to(secret)
        return original_open(path, flags, *args)

    monkeypatch.setattr(write_tools.os, "open", swap_then_open)
    with pytest.raises(ValidationError, match="regular file"):
        await upload_document(
            OGMClient(settings),
            "personal-safe",
            "00000000-0000-0000-0000-000000000002",
            str(source),
            None,
            None,
            (tmp_path.resolve(),),
        )
