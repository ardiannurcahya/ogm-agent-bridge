import httpx
import pytest

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.config import Settings
from ogm_agent_bridge.errors import AuthenticationError, TimeoutError


@pytest.fixture
def settings() -> Settings:
    return Settings("https://core.example.test", "api-key", "project-id", 1, 1)


@pytest.mark.asyncio
async def test_sends_project_auth_headers(settings: Settings) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-API-Key"] == "api-key"
        assert request.headers["X-Project-Id"] == "project-id"
        assert request.url.path == "/v1/health"
        return httpx.Response(200, json={"ok": True})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = OGMClient(settings, http_client)
        response = await client.request("GET", "/v1/health")

    assert response.json() == {"ok": True}


@pytest.mark.asyncio
async def test_retries_retryable_status(settings: Settings) -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503 if calls == 1 else 200)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        response = await OGMClient(settings, http_client).request("GET", "/v1/health")

    assert response.status_code == 200
    assert calls == 2


@pytest.mark.asyncio
async def test_maps_http_errors(settings: Settings) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "bad key"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(AuthenticationError, match="bad key"):
            await OGMClient(settings, http_client).request("GET", "/v1/health")


@pytest.mark.asyncio
async def test_retries_timeout_then_maps_timeout(settings: Settings) -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("slow", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(TimeoutError):
            await OGMClient(settings, http_client).request("GET", "/v1/health")

    assert calls == 2
