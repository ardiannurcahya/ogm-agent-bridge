import asyncio
import datetime
import email.utils

import httpx
import pytest

from ogm_mcp_skills.client import OGMClient, _retry_after
from ogm_mcp_skills.config import Settings
from ogm_mcp_skills.errors import (
    AmbiguousWriteError,
    AuthenticationError,
    ConflictError,
    RateLimitError,
    TimeoutError,
    UpstreamError,
    ValidationError,
)


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
async def test_preserves_base_url_path_prefix() -> None:
    settings = Settings("https://core.example.test/api", "api-key", "project-id")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/health"
        return httpx.Response(200, json={"ok": True})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        response = await OGMClient(settings, http_client).request("GET", "/v1/health")

    assert response.json() == {"ok": True}


@pytest.mark.asyncio
async def test_rejects_successful_non_json_response(settings: Settings) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>frontend</html>")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(UpstreamError, match="non-JSON response"):
            await OGMClient(settings, http_client).request("GET", "/v1/health")


@pytest.mark.asyncio
async def test_retries_retryable_status(settings: Settings) -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503)
        return httpx.Response(200, json={"ok": True})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        response = await OGMClient(settings, http_client).request("GET", "/v1/health")

    assert response.status_code == 200
    assert calls == 2


@pytest.mark.asyncio
async def test_maps_http_errors(settings: Settings) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "bad key"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(AuthenticationError) as caught:
            await OGMClient(settings, http_client).request("GET", "/v1/health")
    assert "bad key" not in str(caught.value)


@pytest.mark.asyncio
async def test_rejects_redirect_json_response_and_closes_it(settings: Settings) -> None:
    upstream_response: httpx.Response | None = None

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal upstream_response
        upstream_response = httpx.Response(302, json={"detail": "private redirect"})
        return upstream_response

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(UpstreamError) as caught:
            await OGMClient(settings, http_client).request("GET", "/v1/health")

    assert "private redirect" not in str(caught.value)
    assert upstream_response is not None
    assert upstream_response.is_closed


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "error"),
    [
        (408, TimeoutError),
        (409, ConflictError),
        (422, ValidationError),
        (429, RateLimitError),
        (500, UpstreamError),
    ],
)
async def test_maps_audited_statuses(
    settings: Settings, status: int, error: type[Exception]
) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"detail": "private upstream exception"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(error) as caught:
            await OGMClient(settings, http_client).request(
                "GET", "/v1/health", retry=False
            )
    assert "private upstream exception" not in str(caught.value)


@pytest.mark.asyncio
async def test_retries_safe_request_using_bounded_retry_after(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0
    delays: list[float] = []

    async def sleep(delay: float) -> None:
        delays.append(delay)

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "999"})
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(asyncio, "sleep", sleep)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        response = await OGMClient(settings, http_client).request("GET", "/v1/health")
    assert response.status_code == 200
    assert calls == 2
    assert delays == [30.0]


@pytest.mark.asyncio
async def test_non_idempotent_write_never_retries_or_exposes_upstream_detail(
    settings: Settings,
) -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503, json={"detail": "sensitive trace"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(UpstreamError) as caught:
            await OGMClient(settings, http_client).request("POST", "/v1/write")
    assert calls == 1
    assert "sensitive trace" not in str(caught.value)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "error"),
    [
        (408, TimeoutError),
        (409, ConflictError),
        (422, ValidationError),
        (429, RateLimitError),
        (500, AmbiguousWriteError),
        (502, AmbiguousWriteError),
        (503, AmbiguousWriteError),
        (504, AmbiguousWriteError),
    ],
)
async def test_ambiguous_write_status_matrix_is_single_attempt(
    settings: Settings, status: int, error: type[Exception]
) -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(status, json={"detail": "private upstream exception"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(error) as caught:
            await OGMClient(settings, http_client).request(
                "POST", "/v1/write", ambiguous_write=True
            )

    assert calls == 1
    assert "private upstream exception" not in str(caught.value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1.5", 1.5),
        ("-1", None),
        ("999", 30.0),
        ("nan", None),
        ("inf", None),
        ("not-a-date", None),
    ],
)
def test_retry_after_numeric_and_malformed_values(
    value: str, expected: float | None
) -> None:
    assert _retry_after(httpx.Response(429, headers={"Retry-After": value})) == expected


def test_retry_after_http_date_is_parsed_and_bounded() -> None:
    future = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=90)
    header = email.utils.format_datetime(future, usegmt=True)

    delay = _retry_after(httpx.Response(503, headers={"Retry-After": header}))

    assert delay == 30.0


def test_retry_after_past_http_date_has_no_delay() -> None:
    past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=90)  # noqa: UP017
    header = email.utils.format_datetime(past, usegmt=True)

    assert _retry_after(httpx.Response(503, headers={"Retry-After": header})) == 0.0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "error"),
    [
        (429, RateLimitError),
        (502, UpstreamError),
        (503, UpstreamError),
        (504, UpstreamError),
    ],
)
async def test_retries_all_retryable_statuses_until_exhaustion(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    error: type[Exception],
) -> None:
    calls = 0
    delays: list[float] = []

    async def sleep(delay: float) -> None:
        delays.append(delay)

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(status)

    monkeypatch.setattr(asyncio, "sleep", sleep)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(error):
            await OGMClient(settings, http_client).request("GET", "/v1/health")

    assert calls == settings.max_retries + 1
    assert delays == [0.1] * settings.max_retries
