"""Graph-first read-tool handlers and core input validation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.errors import ValidationError
from ogm_agent_bridge.permissions import require_read
from ogm_agent_bridge.responses import envelope


async def list_datasets(client: OGMClient) -> dict[str, Any]:
    require_read("datasets:read")
    response = await client.request("GET", "/v1/datasets")
    return envelope(response.json(), provenance={"project_id": client.project_id})


async def search_entities(
    client: OGMClient, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    dataset_id = _string(arguments, "dataset_id", 1)
    params = {"q": _string(arguments, "q", 1, 200)}
    _optional_string(arguments, params, "entity_type", 100)
    _integer(arguments, params, "limit", 1, 100)
    return await _get(
        client, f"/v1/datasets/{dataset_id}/entities/search", params, dataset_id
    )


async def get_entity(client: OGMClient, entity_id: str) -> dict[str, Any]:
    return await _get(
        client, f"/v1/entities/{_value(entity_id, 'entity_id', 1)}", {}, None, entity_id
    )


async def get_neighbors(
    client: OGMClient, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    entity_id = _string(arguments, "entity_id", 1)
    params: dict[str, Any] = {}
    _integer(arguments, params, "limit", 1, 100)
    return await _get(
        client, f"/v1/entities/{entity_id}/neighbors", params, None, entity_id
    )


async def find_path(client: OGMClient, arguments: Mapping[str, Any]) -> dict[str, Any]:
    dataset_id = _string(arguments, "dataset_id", 1)
    params = {
        "source_entity_id": _string(arguments, "source_entity_id", 1),
        "target_entity_id": _string(arguments, "target_entity_id", 1),
    }
    _integer(arguments, params, "max_depth", 1, 4)
    _integer(arguments, params, "relation_limit", 1, 200)
    return await _get(
        client, f"/v1/datasets/{dataset_id}/graph/path", params, dataset_id
    )


async def get_subgraph(
    client: OGMClient, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    dataset_id = _string(arguments, "dataset_id", 1)
    params = {"entity_id": _string(arguments, "entity_id", 1)}
    _integer(arguments, params, "depth", 0, 2)
    _integer(arguments, params, "node_limit", 1, 200)
    _integer(arguments, params, "relation_limit", 1, 400)
    return await _get(
        client, f"/v1/datasets/{dataset_id}/graph/subgraph", params, dataset_id
    )


async def get_graph(client: OGMClient, arguments: Mapping[str, Any]) -> dict[str, Any]:
    dataset_id = _string(arguments, "dataset_id", 1)
    params: dict[str, Any] = {}
    _integer(arguments, params, "limit", 1, 200)
    _integer(arguments, params, "depth", 0, 1)
    return await _get(client, f"/v1/datasets/{dataset_id}/graph", params, dataset_id)


async def get_evidence(client: OGMClient, evidence_id: str) -> dict[str, Any]:
    return await _get(
        client,
        f"/v1/evidence/{_value(evidence_id, 'evidence_id', 1)}",
        {},
        None,
        None,
        evidence_id,
    )


async def get_relation_evidence(
    client: OGMClient, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    dataset_id = _string(arguments, "dataset_id", 1)
    relation_id = _string(arguments, "relation_id", 1)
    params: dict[str, Any] = {}
    _integer(arguments, params, "limit", 1, 100)
    return await _get(
        client,
        f"/v1/datasets/{dataset_id}/relations/{relation_id}/evidence",
        params,
        dataset_id,
        None,
        None,
        relation_id,
    )


async def _get(
    client: OGMClient,
    path: str,
    params: Mapping[str, Any],
    dataset_id: str | None,
    entity_id: str | None = None,
    evidence_id: str | None = None,
    relation_id: str | None = None,
) -> dict[str, Any]:
    require_read("graph:read")
    response = await client.request("GET", path, params=params or None)
    provenance: dict[str, str] = {"project_id": client.project_id}
    for key, value in (
        ("dataset_id", dataset_id),
        ("entity_id", entity_id),
        ("evidence_id", evidence_id),
        ("relation_id", relation_id),
    ):
        if value is not None:
            provenance[key] = value
    return envelope(response.json(), provenance=provenance)


def _string(
    arguments: Mapping[str, Any], name: str, minimum: int, maximum: int | None = None
) -> str:
    return _value(arguments.get(name), name, minimum, maximum)


def _value(value: object, name: str, minimum: int, maximum: int | None = None) -> str:
    if (
        type(value) is not str
        or len(value) < minimum
        or (maximum is not None and len(value) > maximum)
    ):
        raise ValidationError(f"{name} has invalid length")
    return value


def _integer(
    arguments: Mapping[str, Any],
    target: dict[str, Any],
    name: str,
    minimum: int,
    maximum: int,
) -> None:
    if name not in arguments:
        return
    value = arguments[name]
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValidationError(f"{name} must be an integer from {minimum} to {maximum}")
    target[name] = value


def _optional_string(
    arguments: Mapping[str, Any], target: dict[str, Any], name: str, maximum: int
) -> None:
    if name in arguments:
        target[name] = _value(arguments[name], name, 1, maximum)
