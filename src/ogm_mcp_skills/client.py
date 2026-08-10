"""Async OpenGraphMemory HTTP client."""

from __future__ import annotations

import asyncio
import datetime
import email.utils
import math
from collections.abc import Mapping
from typing import Any

import httpx

from ogm_mcp_skills.config import Settings
from ogm_mcp_skills.errors import (
    AmbiguousWriteError,
    TimeoutError,
    TransportError,
    UpstreamError,
    error_from_status,
)

_RETRYABLE_STATUS_CODES = frozenset({429, 502, 503, 504})
_MAX_RETRY_AFTER_SECONDS = 30.0
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


class OGMClient:
    """Project-scoped core API client with bounded retries."""

    def __init__(
        self, settings: Settings, client: httpx.AsyncClient | None = None
    ) -> None:
        self._settings = settings
        self._client = client or httpx.AsyncClient(
            base_url=settings.base_url, timeout=httpx.Timeout(settings.timeout_seconds)
        )
        self._owns_client = client is None

    async def __aenter__(self) -> OGMClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    @property
    def project_id(self) -> str:
        return self._settings.project_id

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
        files: Any = None,
        authenticated: bool = True,
        retry: bool = True,
        ambiguous_write: bool = False,
    ) -> httpx.Response:
        """Send a request, retrying only bounded safe/read operations."""
        headers = (
            {
                "X-API-Key": self._settings.api_key,
                "X-Project-Id": self._settings.project_id,
            }
            if authenticated
            else {}
        )
        is_safe_request = method.upper() in _SAFE_METHODS
        retries = self._settings.max_retries if retry and is_safe_request else 0
        for attempt in range(retries + 1):
            try:
                response = await self._client.request(
                    method,
                    f"{self._settings.base_url.rstrip('/')}/{path.lstrip('/')}",
                    headers=headers,
                    json=json,
                    params=params,
                    data=data,
                    files=files,
                )
            except httpx.TimeoutException as error:
                if attempt == retries:
                    if ambiguous_write:
                        raise AmbiguousWriteError(
                            "Core API write may have succeeded"
                        ) from error
                    raise TimeoutError("Core API request timed out") from error
                await _sleep_before_retry(None)
                continue
            except httpx.RequestError as error:
                if attempt == retries:
                    if ambiguous_write:
                        raise AmbiguousWriteError(
                            "Core API write may have succeeded"
                        ) from error
                    raise TransportError("Core API transport failed") from error
                await _sleep_before_retry(None)
                continue
            # A server error can occur after Core accepted a non-idempotent
            # write.  Rate limiting and client errors, however, have definite
            # outcomes and retain their normal public error mappings.
            if ambiguous_write and 500 <= response.status_code <= 599:
                await response.aclose()
                raise AmbiguousWriteError("Core API write outcome is unknown")
            if response.status_code in _RETRYABLE_STATUS_CODES and attempt < retries:
                delay = _retry_after(response)
                await response.aclose()
                await _sleep_before_retry(delay)
                continue
            if not 200 <= response.status_code <= 299:
                await response.aclose()
                raise error_from_status(response.status_code)
            try:
                response.json()
            except ValueError as error:
                await response.aclose()
                raise UpstreamError("Core API returned a non-JSON response") from error
            return response
        raise AssertionError("retry loop must return or raise")


def _retry_after(response: httpx.Response) -> float | None:
    """Parse Retry-After without trusting malformed or unbounded values."""
    value = response.headers.get("Retry-After")
    if value is None:
        return None
    try:
        delay = float(value)
    except (TypeError, ValueError):
        try:
            retry_at = email.utils.parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=datetime.UTC)
        delay = (retry_at - datetime.datetime.now(datetime.UTC)).total_seconds()
        delay = max(0.0, delay)
    if not math.isfinite(delay) or delay < 0:
        return None
    return min(_MAX_RETRY_AFTER_SECONDS, delay)


async def _sleep_before_retry(delay: float | None) -> None:
    # A short bounded fallback prevents immediate retry storms when no hint exists.
    await asyncio.sleep(0.1 if delay is None else delay)
