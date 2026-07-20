"""Async OpenGraphMemory HTTP client."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from ogm_agent_bridge.config import Settings
from ogm_agent_bridge.errors import (
    AmbiguousWriteError,
    TimeoutError,
    TransportError,
    UpstreamError,
    error_from_status,
)

_RETRYABLE_STATUS_CODES = frozenset({502, 503})


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
        """Send core request; callers disable retry for non-idempotent writes."""
        headers = (
            {
                "X-API-Key": self._settings.api_key,
                "X-Project-Id": self._settings.project_id,
            }
            if authenticated
            else {}
        )
        retries = self._settings.max_retries if retry else 0
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
                continue
            except httpx.RequestError as error:
                if attempt == retries:
                    if ambiguous_write:
                        raise AmbiguousWriteError(
                            "Core API write may have succeeded"
                        ) from error
                    raise TransportError("Core API transport failed") from error
                continue
            if response.status_code in _RETRYABLE_STATUS_CODES and ambiguous_write:
                message = _message(response)
                await response.aclose()
                raise AmbiguousWriteError(message)
            if response.status_code in _RETRYABLE_STATUS_CODES and attempt < retries:
                await response.aclose()
                continue
            if response.is_error:
                message = _message(response)
                await response.aclose()
                raise error_from_status(response.status_code, message)
            try:
                response.json()
            except ValueError as error:
                await response.aclose()
                raise UpstreamError("Core API returned a non-JSON response") from error
            return response
        raise AssertionError("retry loop must return or raise")


def _message(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return "Core API request failed"
    detail = body.get("detail") if isinstance(body, dict) else None
    return detail if isinstance(detail, str) else "Core API request failed"
