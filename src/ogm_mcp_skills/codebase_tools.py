"""Codebase Knowledge Graph & Agent Memory tool handlers for ogm-mcp-skills."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ogm_mcp_skills.client import OGMClient
from ogm_mcp_skills.errors import ValidationError
from ogm_mcp_skills.permissions import (
    require_memory_read,
    require_memory_write,
    require_read,
    require_write,
)
from ogm_mcp_skills.responses import envelope
from ogm_mcp_skills.tools import (
    _arguments,
    _get,
    _integer,
    _optional_string,
    _route_component,
    _string,
)


async def search_code_symbols(
    client: OGMClient, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    """Search codebase entities (functions, classes, interfaces, structs) in a dataset."""
    require_read("graph:read")
    _arguments(arguments, {"dataset_id", "q", "kind", "language", "file_path", "limit"})
    dataset_id = _route_component(arguments.get("dataset_id"), "dataset_id", 1)
    params = {"q": _string(arguments, "q", 1, 200)}
    _optional_string(arguments, params, "kind", 50)
    _optional_string(arguments, params, "language", 50)
    _optional_string(arguments, params, "file_path", 500)
    _integer(arguments, params, "limit", 1, 100)

    return await _get(
        client, f"/v1/datasets/{dataset_id}/entities/search", params, dataset_id
    )


async def get_code_call_graph(
    client: OGMClient, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    """Inspect callers, calls, and inheritance for a code symbol."""
    require_read("graph:read")
    _arguments(arguments, {"entity_id", "limit"})
    entity_id = _route_component(arguments.get("entity_id"), "entity_id", 1)
    params: dict[str, Any] = {}
    _integer(arguments, params, "limit", 1, 100)
    return await _get(
        client, f"/v1/entities/{entity_id}/neighbors", params, None, entity_id
    )


async def get_code_chunks(
    client: OGMClient, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    """Fetch AST structural code chunks with line bounds for a dataset/document."""
    require_read("graph:read")
    _arguments(arguments, {"dataset_id", "file_path", "limit"})
    dataset_id = _route_component(arguments.get("dataset_id"), "dataset_id", 1)
    params: dict[str, Any] = {}
    _optional_string(arguments, params, "file_path", 500)
    _integer(arguments, params, "limit", 1, 100)
    return await _get(
        client, f"/v1/datasets/{dataset_id}/graph/explorer/nodes", params, dataset_id
    )


async def recall_code_memory(
    client: OGMClient, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    """Recall past agent bugfixes and refactoring memories for a code file or function."""
    require_memory_read()

    _arguments(arguments, {"file_path", "function_name", "q", "limit"})
    query_str = (
        arguments.get("q")
        or arguments.get("file_path")
        or arguments.get("function_name")
    )
    if not query_str:
        raise ValidationError(
            "at least one of 'q', 'file_path', or 'function_name' is required"
        )
    params = {"q": str(query_str)[:200]}
    _optional_string(arguments, params, "file_path", 500)
    _integer(arguments, params, "limit", 1, 50)
    response = await client.request("GET", "/v1/agent-memory/search", params=params)
    return envelope(response.json(), provenance={"project_id": client.project_id})


async def record_code_fix(
    client: OGMClient, profile: str, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    """Record an agent memory episode for a codebase bug fix or refactor."""
    require_memory_write(profile, "agent-memory:write")

    _arguments(
        arguments,
        {
            "file_path",
            "title",
            "goal",
            "root_cause",
            "solution",
            "function_name",
            "idempotency_key",
        },
    )
    file_path = _string(arguments, "file_path", 1, 500)
    title = _string(arguments, "title", 1, 255)
    goal = _string(arguments, "goal", 1, 1000)
    root_cause = _string(arguments, "root_cause", 1, 2000)
    solution = _string(arguments, "solution", 1, 2000)
    func_name = arguments.get("function_name")

    payload = {
        "domain": "engineering",
        "type": "bugfix",
        "title": title,
        "goal": goal,
        "problem_signature": f"{file_path}:{func_name}" if func_name else file_path,
        "scope": {
            "file_path": file_path,
            "function_name": func_name,
        },
        "content": {
            "root_cause": root_cause,
            "solution": solution,
        },
        "confidence": 1.0,
        "idempotency_key": arguments.get("idempotency_key"),
    }
    response = await client.request("POST", "/v1/agent-memory/episodes", json=payload)
    return envelope(response.json(), provenance={"project_id": client.project_id})


async def sync_code_file(
    client: OGMClient, profile: str, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    """Sync a single edited code file into the Knowledge Graph in real-time."""
    require_write(profile, "documents:write")

    _arguments(arguments, {"dataset_id", "file_path", "code", "language"})
    dataset_id = _route_component(arguments.get("dataset_id"), "dataset_id", 1)
    file_path = _string(arguments, "file_path", 1, 500)
    code = _string(arguments, "code", 1, 500000)
    language = arguments.get("language")

    payload = {
        "dataset_id": dataset_id,
        "file_path": file_path,
        "code": code,
        "language": language,
    }
    response = await client.request("POST", "/v1/codebase/sync-file", json=payload)
    return envelope(response.json(), provenance={"project_id": client.project_id})
