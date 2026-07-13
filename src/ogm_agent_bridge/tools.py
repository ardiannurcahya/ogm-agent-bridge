"""B1 read-tool handlers and core input validation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.errors import ValidationError
from ogm_agent_bridge.permissions import require_read
from ogm_agent_bridge.responses import envelope

_MODES = frozenset({"vector_only", "graph_only", "hybrid"})
_FUSIONS = frozenset({"rrf", "weighted"})
_SCOPES = frozenset({"user", "agent", "session"})


async def list_datasets(client: OGMClient) -> dict[str, Any]:
    """List datasets in configured project."""
    require_read("datasets:read")
    response = await client.request("GET", "/v1/datasets")
    return envelope(response.json(), provenance={"project_id": client.project_id})


async def query(client: OGMClient, arguments: Mapping[str, Any]) -> dict[str, Any]:
    """Run grounded retrieval and preserve core response exactly."""
    require_read("query:read")
    payload: dict[str, Any] = {
        "dataset_id": _string(arguments, "dataset_id", 1),
        "query": _string(arguments, "query", 1, 10_000),
    }
    _choice(arguments, payload, "mode", _MODES)
    _integer(arguments, payload, "top_k", 1, 50)
    _integer(arguments, payload, "graph_depth", 1, 2)
    _integer(arguments, payload, "graph_fanout", 1, 100)
    _integer(arguments, payload, "graph_timeout_ms", 1, 10_000)
    _choice(arguments, payload, "fusion", _FUSIONS)
    _optional_string(arguments, payload, "memory_user_id")
    _optional_string(arguments, payload, "memory_agent_id")
    _optional_string(arguments, payload, "memory_session_id")
    _integer(arguments, payload, "memory_top_k", 0, 20)
    response = await client.request("POST", "/v1/query", json=payload)
    data = response.json()
    provenance: dict[str, Any] = {
        "project_id": client.project_id,
        "dataset_id": payload["dataset_id"],
    }
    if isinstance(data, dict) and isinstance(data.get("retrieval_trace"), dict):
        trace_id = data["retrieval_trace"].get("trace_id")
        if isinstance(trace_id, str):
            provenance["trace_id"] = trace_id
    return envelope(data, provenance=provenance)


async def search_memory(
    client: OGMClient, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    """Search memory facts with lexical-search warning."""
    require_read("memory:read")
    payload: dict[str, Any] = {"query": _string(arguments, "query", 1, 5_000)}
    _optional_string(arguments, payload, "user_id")
    _optional_string(arguments, payload, "agent_id")
    _optional_string(arguments, payload, "session_id")
    _integer(arguments, payload, "limit", 1, 50)
    if "include_superseded" in arguments:
        value = arguments["include_superseded"]
        if type(value) is not bool:
            raise ValidationError("include_superseded must be a boolean")
        payload["include_superseded"] = value
    if "scopes" in arguments:
        scopes = arguments["scopes"]
        if not isinstance(scopes, list) or not all(
            type(scope) is str and scope in _SCOPES for scope in scopes
        ):
            raise ValidationError("scopes must contain user, agent, or session")
        payload["scopes"] = scopes
    response = await client.request("POST", "/v1/memory/search", json=payload)
    return envelope(
        response.json(),
        provenance={"project_id": client.project_id},
        warnings=["Memory search is lexical, not semantic retrieval."],
    )


def _string(
    arguments: Mapping[str, Any], name: str, minimum: int, maximum: int | None = None
) -> str:
    value = arguments.get(name)
    if (
        type(value) is not str
        or len(value) < minimum
        or (maximum is not None and len(value) > maximum)
    ):
        raise ValidationError(f"{name} has invalid length")
    return value


def _integer(
    arguments: Mapping[str, Any],
    payload: dict[str, Any],
    name: str,
    minimum: int,
    maximum: int,
) -> None:
    if name not in arguments:
        return
    value = arguments[name]
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValidationError(f"{name} must be an integer from {minimum} to {maximum}")
    payload[name] = value


def _optional_string(
    arguments: Mapping[str, Any], payload: dict[str, Any], name: str
) -> None:
    if name not in arguments:
        return
    value = arguments[name]
    if type(value) is not str or not value:
        raise ValidationError(f"{name} must be a non-empty string")
    payload[name] = value


def _choice(
    arguments: Mapping[str, Any],
    payload: dict[str, Any],
    name: str,
    choices: frozenset[str],
) -> None:
    if name not in arguments:
        return
    value = arguments[name]
    if type(value) is not str or value not in choices:
        raise ValidationError(f"{name} is invalid")
    payload[name] = value
