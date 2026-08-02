import json

import httpx
import pytest

from ogm_agent_bridge.agent_memory_tools import (
    append_attempt,
    create_episode,
    feedback_episode,
    feedback_pattern,
    get_episode,
    list_episodes,
    record_outcome,
    search,
    supersede_episode,
    supersede_pattern,
)
from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.config import Settings
from ogm_agent_bridge.errors import (
    AmbiguousWriteError,
    PermissionError,
    ValidationError,
)

EPISODE_ID = "mem_019f8062-5644-78c6-8936-de3dcf331302"
REPLACEMENT_ID = "mem_019f8062-5644-78c6-8936-de3dcf331303"


@pytest.fixture
def settings() -> Settings:
    return Settings("https://core.example.test", "api-key", "project-id")


@pytest.mark.asyncio
async def test_memory_reads_preserve_payload_headers_filters_and_warning(
    settings: Settings,
) -> None:
    calls: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("/search"):
            return httpx.Response(
                200, json={"query": "redis", "results": [{"id": "memory"}]}
            )
        return httpx.Response(200, json=[{"id": "memory"}])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = OGMClient(settings, http_client)
        listed = await list_episodes(client, {"status": "active", "limit": 5})
        found = await search(
            client,
            {"q": "redis", "repository": "ogm", "include_inactive": False},
        )
        episode = await get_episode(client, EPISODE_ID)

    assert [(request.method, request.url.path) for request in calls] == [
        ("GET", "/v1/agent-memory/episodes"),
        ("GET", "/v1/agent-memory/search"),
        ("GET", f"/v1/agent-memory/episodes/{EPISODE_ID}"),
    ]
    assert calls[0].url.query.decode() == "status=active&limit=5"
    assert (
        calls[1].url.query.decode() == "q=redis&repository=ogm&include_inactive=false"
    )
    assert all(request.headers["X-API-Key"] == "api-key" for request in calls)
    assert all(request.headers["X-Project-Id"] == "project-id" for request in calls)
    assert listed["data"] == [{"id": "memory"}]
    assert episode["provenance"]["episode_id"] == EPISODE_ID
    assert found["warnings"]


@pytest.mark.asyncio
async def test_memory_writes_send_exact_bounded_payload_without_retry(
    settings: Settings,
) -> None:
    calls: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(201, json={"id": "memory-result"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = OGMClient(settings, http_client)
        created = await create_episode(
            client,
            "personal-safe",
            {
                "domain": "engineering",
                "title": "Redis timeout",
                "goal": "Restore workers",
                "problem_signature": "redis-timeout",
                "tags": ["redis"],
                "evidence": [{"reference": "runtime://logs"}],
            },
        )
        attempted = await append_attempt(
            client,
            "personal-safe",
            EPISODE_ID,
            {
                "hypothesis": "pool exhausted",
                "result": "success",
                "actions": ["restart"],
            },
        )
        outcome = await record_outcome(
            client,
            "personal-safe",
            EPISODE_ID,
            {
                "status": "success",
                "summary": "restored",
                "verifiers": [{"kind": "runtime", "name": "ready", "status": "passed"}],
            },
        )

    assert [request.url.path for request in calls] == [
        "/v1/agent-memory/episodes",
        f"/v1/agent-memory/episodes/{EPISODE_ID}/attempts",
        f"/v1/agent-memory/episodes/{EPISODE_ID}/outcomes",
    ]
    assert json.loads(calls[0].content) == {
        "domain": "engineering",
        "title": "Redis timeout",
        "goal": "Restore workers",
        "problem_signature": "redis-timeout",
        "scope": {},
        "tags": ["redis"],
        "metadata": {},
        "evidence": [{"reference": "runtime://logs", "metadata": {}}],
    }
    assert (
        created["data"]
        == attempted["data"]
        == outcome["data"]
        == {"id": "memory-result"}
    )


@pytest.mark.asyncio
async def test_memory_write_503_is_ambiguous_and_never_retried(
    settings: Settings,
) -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503, json={"detail": "gateway unavailable"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(AmbiguousWriteError):
            await feedback_episode(
                OGMClient(settings, http_client), "memory-curator", EPISODE_ID, 1
            )
    assert calls == 1


@pytest.mark.asyncio
async def test_memory_write_timeout_is_ambiguous_and_never_retried(
    settings: Settings,
) -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("slow", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(AmbiguousWriteError):
            await feedback_episode(
                OGMClient(settings, http_client), "memory-curator", EPISODE_ID, 1
            )
    assert calls == 1


@pytest.mark.asyncio
async def test_memory_permissions_and_validation_are_local(settings: Settings) -> None:
    client = OGMClient(settings)
    with pytest.raises(PermissionError):
        await create_episode(
            client,
            "read-only",
            {
                "domain": "engineering",
                "title": "x",
                "goal": "x",
                "problem_signature": "x",
            },
        )
    with pytest.raises(PermissionError):
        await feedback_episode(client, "personal-safe", EPISODE_ID, 1)
    with pytest.raises(ValidationError):
        await get_episode(client, "episode-1")
    with pytest.raises(ValidationError):
        await search(client, {"q": " "})
    with pytest.raises(ValidationError):
        await list_episodes(client, {"limit": True})
    with pytest.raises(ValidationError):
        await supersede_pattern(client, "memory-curator", "same", "same")
    await client.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "selector",
    [
        f"{EPISODE_ID}?redirect=x",
        f"{EPISODE_ID}#fragment",
        f"{EPISODE_ID}%2fescape",
        f"{EPISODE_ID}&x=1",
        f"{EPISODE_ID}/escape",
        f"{EPISODE_ID}\\escape",
        f"{EPISODE_ID}\nvalue",
        f"{EPISODE_ID}\x00value",
    ],
)
async def test_memory_rejects_delimiter_and_encoded_route_injection(
    settings: Settings, selector: str
) -> None:
    with pytest.raises(ValidationError):
        await get_episode(OGMClient(settings), selector)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "selector",
    [
        f"{EPISODE_ID}?redirect=x",
        f"{EPISODE_ID}#fragment",
        f"{EPISODE_ID}%2fescape",
        f"{EPISODE_ID}&x=1",
        f"{EPISODE_ID}/escape",
        f"{EPISODE_ID}\\escape",
        f"{EPISODE_ID}\nvalue",
        f"{EPISODE_ID}\x00value",
    ],
)
@pytest.mark.parametrize(
    "handler",
    [
        lambda client, value: append_attempt(
            client,
            "personal-safe",
            value,
            {"hypothesis": "h", "result": "success"},
        ),
        lambda client, value: record_outcome(
            client, "personal-safe", value, {"status": "success", "summary": "s"}
        ),
        lambda client, value: feedback_episode(client, "memory-curator", value, 1),
        lambda client, value: supersede_episode(
            client, "memory-curator", value, REPLACEMENT_ID
        ),
        lambda client, value: supersede_episode(
            client, "memory-curator", EPISODE_ID, value
        ),
    ],
)
async def test_memory_rejects_episode_id_route_injection_every_handler(
    settings: Settings, selector: str, handler
) -> None:
    with pytest.raises(ValidationError):
        await handler(OGMClient(settings), selector)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "selector",
    [
        "pattern?redirect=x",
        "pattern#fragment",
        "pattern%2fescape",
        "pattern&x=1",
        "pattern/escape",
        "pattern\\escape",
        "pattern\nvalue",
        "pattern\x00value",
    ],
)
@pytest.mark.parametrize(
    "handler",
    [
        lambda client, value: feedback_pattern(client, "memory-curator", value, 1),
        lambda client, value: supersede_pattern(
            client, "memory-curator", value, "replacement"
        ),
        lambda client, value: supersede_pattern(
            client, "memory-curator", "pattern", value
        ),
    ],
)
async def test_memory_rejects_pattern_key_route_injection_every_handler(
    settings: Settings, selector: str, handler
) -> None:
    with pytest.raises(ValidationError):
        await handler(OGMClient(settings), selector)
