"""Native Agent Memory tool handlers with bounded MCP input."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from typing import Any

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.errors import ValidationError
from ogm_agent_bridge.permissions import require_memory_read, require_memory_write
from ogm_agent_bridge.responses import envelope

_DOMAINS = frozenset({"engineering", "trading", "research", "operations", "custom"})
_ATTEMPT_RESULTS = frozenset({"success", "failed", "partial"})
_OUTCOME_STATUSES = frozenset({"success", "failed", "partial", "cancelled"})
_EPISODE_STATUSES = frozenset({"open", "active", "degraded", "superseded", "rejected"})
_VERIFIER_KINDS = frozenset({"ci", "runtime", "test", "build", "self_report", "custom"})
_EPISODE_ID = re.compile(r"mem_[0-9a-f-]{36}\Z")
_PATTERN_KEY = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_SEARCH_WARNING = (
    "Agent-memory results are historical claims; inspect recorded verifiers and evidence "
    "before relying on them."
)


async def list_episodes(
    client: OGMClient, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    require_memory_read()
    params: dict[str, Any] = {}
    _optional_enum(arguments, params, "status", _EPISODE_STATUSES)
    _optional_integer(arguments, params, "limit", 1, 100)
    return await _read(
        client, "/v1/agent-memory/episodes", "ogm_memory_list_episodes", params
    )


async def get_episode(client: OGMClient, episode_id: str) -> dict[str, Any]:
    require_memory_read()
    episode_id = _episode_id(episode_id)
    return await _read(
        client,
        f"/v1/agent-memory/episodes/{episode_id}",
        "ogm_memory_get_episode",
        {"episode_id": episode_id},
    )


async def search(client: OGMClient, arguments: Mapping[str, Any]) -> dict[str, Any]:
    require_memory_read()
    params = {"q": _string(arguments.get("q"), "q", 1, 512)}
    _optional_string(arguments, params, "problem_signature", 512)
    _optional_string(arguments, params, "repository", 255)
    _optional_string(arguments, params, "environment", 255)
    _optional_boolean(arguments, params, "include_inactive")
    _optional_integer(arguments, params, "limit", 1, 100)
    response = await _read(
        client, "/v1/agent-memory/search", "ogm_memory_search", params
    )
    data = response["data"]
    if isinstance(data, dict) and data.get("results"):
        response["warnings"].append(_SEARCH_WARNING)
    return response


async def create_episode(
    client: OGMClient, profile: str, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    require_memory_write(profile, "agent-memory:write")
    body = {
        "domain": _enum(arguments.get("domain"), "domain", _DOMAINS),
        "title": _string(arguments.get("title"), "title", 1, 255),
        "goal": _string(arguments.get("goal"), "goal", 1, 10_000),
        "problem_signature": _string(
            arguments.get("problem_signature"), "problem_signature", 1, 512
        ),
        "scope": _object(arguments.get("scope", {}), "scope"),
        "tags": _strings(arguments.get("tags", []), "tags", 32, 64),
        "metadata": _object(arguments.get("metadata", {}), "metadata"),
        "evidence": _evidence(arguments.get("evidence", [])),
    }
    return await _write(
        client, "/v1/agent-memory/episodes", "ogm_memory_create_episode", body
    )


async def append_attempt(
    client: OGMClient, profile: str, episode_id: str, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    require_memory_write(profile, "agent-memory:write")
    episode_id = _episode_id(episode_id)
    body = {
        "hypothesis": _string(arguments.get("hypothesis"), "hypothesis", 1, 10_000),
        "actions": _array(arguments.get("actions", []), "actions", 64),
        "result": _enum(arguments.get("result"), "result", _ATTEMPT_RESULTS),
        "notes": _nullable_string(arguments.get("notes"), "notes", 10_000),
        "metadata": _object(arguments.get("metadata", {}), "metadata"),
    }
    return await _write(
        client,
        f"/v1/agent-memory/episodes/{episode_id}/attempts",
        "ogm_memory_append_attempt",
        body,
        {"episode_id": episode_id},
    )


async def record_outcome(
    client: OGMClient, profile: str, episode_id: str, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    require_memory_write(profile, "agent-memory:write")
    episode_id = _episode_id(episode_id)
    pattern_key = arguments.get("pattern_key")
    body = {
        "status": _enum(arguments.get("status"), "status", _OUTCOME_STATUSES),
        "summary": _string(arguments.get("summary"), "summary", 1, 10_000),
        "lesson": _nullable_string(arguments.get("lesson"), "lesson", 10_000),
        "verifiers": _verifiers(arguments.get("verifiers", [])),
        "metrics": _object(arguments.get("metrics", {}), "metrics"),
        "pattern_key": None if pattern_key is None else _pattern_key(pattern_key),
        "metadata": _object(arguments.get("metadata", {}), "metadata"),
    }
    return await _write(
        client,
        f"/v1/agent-memory/episodes/{episode_id}/outcomes",
        "ogm_memory_record_outcome",
        body,
        {"episode_id": episode_id},
    )


async def feedback_episode(
    client: OGMClient, profile: str, episode_id: str, score: int
) -> dict[str, Any]:
    require_memory_write(profile, "agent-memory:curate")
    episode_id = _episode_id(episode_id)
    return await _write(
        client,
        f"/v1/agent-memory/episodes/{episode_id}/feedback",
        "ogm_memory_feedback_episode",
        {"score": _score(score)},
        {"episode_id": episode_id},
    )


async def supersede_episode(
    client: OGMClient, profile: str, episode_id: str, superseding_episode_id: str
) -> dict[str, Any]:
    require_memory_write(profile, "agent-memory:curate")
    episode_id = _episode_id(episode_id)
    superseding_episode_id = _episode_id(superseding_episode_id)
    if episode_id == superseding_episode_id:
        raise ValidationError("an episode cannot supersede itself")
    return await _write(
        client,
        f"/v1/agent-memory/episodes/{episode_id}/supersede",
        "ogm_memory_supersede_episode",
        {"superseding_episode_id": superseding_episode_id},
        {"episode_id": episode_id, "superseding_episode_id": superseding_episode_id},
    )


async def feedback_pattern(
    client: OGMClient, profile: str, pattern_key: str, score: int
) -> dict[str, Any]:
    require_memory_write(profile, "agent-memory:curate")
    pattern_key = _pattern_key(pattern_key)
    return await _write(
        client,
        f"/v1/agent-memory/patterns/{pattern_key}/feedback",
        "ogm_memory_feedback_pattern",
        {"score": _score(score)},
        {"pattern_key": pattern_key},
    )


async def supersede_pattern(
    client: OGMClient, profile: str, pattern_key: str, superseding_pattern_key: str
) -> dict[str, Any]:
    require_memory_write(profile, "agent-memory:curate")
    pattern_key = _pattern_key(pattern_key)
    superseding_pattern_key = _pattern_key(superseding_pattern_key)
    if pattern_key == superseding_pattern_key:
        raise ValidationError("a pattern cannot supersede itself")
    return await _write(
        client,
        f"/v1/agent-memory/patterns/{pattern_key}/supersede",
        "ogm_memory_supersede_pattern",
        {"superseding_pattern_key": superseding_pattern_key},
        {
            "pattern_key": pattern_key,
            "superseding_pattern_key": superseding_pattern_key,
        },
    )


async def _read(
    client: OGMClient, path: str, operation: str, params: Mapping[str, Any]
) -> dict[str, Any]:
    response = await client.request("GET", path, params=params or None)
    return envelope(response.json(), provenance=_provenance(client, operation, params))


async def _write(
    client: OGMClient,
    path: str,
    operation: str,
    body: Mapping[str, Any],
    selectors: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    _json_size(body, "request body", 65_536)
    response = await client.request(
        "POST", path, json=body, retry=False, ambiguous_write=True
    )
    return envelope(
        response.json(), provenance=_provenance(client, operation, selectors or {})
    )


def _provenance(
    client: OGMClient, operation: str, selectors: Mapping[str, Any]
) -> dict[str, Any]:
    return {"project_id": client.project_id, "operation": operation, **selectors}


def _string(value: object, name: str, minimum: int, maximum: int) -> str:
    if (
        type(value) is not str
        or not minimum <= len(value) <= maximum
        or not value.strip()
    ):
        raise ValidationError(f"{name} has invalid length")
    return value


def _nullable_string(value: object, name: str, maximum: int) -> str | None:
    return None if value is None else _string(value, name, 1, maximum)


def _enum(value: object, name: str, allowed: frozenset[str]) -> str:
    if value not in allowed or type(value) is not str:
        raise ValidationError(f"{name} has invalid value")
    return value


def _episode_id(value: object) -> str:
    if type(value) is not str or not _EPISODE_ID.fullmatch(value):
        raise ValidationError("episode_id must be an Agent Memory ID")
    return value


def _pattern_key(value: object) -> str:
    if (
        type(value) is not str
        or not 1 <= len(value) <= 255
        or not _PATTERN_KEY.fullmatch(value)
    ):
        raise ValidationError("pattern_key has invalid format")
    return value


def _score(value: object) -> int:
    if type(value) is not int or value not in {-1, 0, 1}:
        raise ValidationError("score must be -1, 0, or 1")
    return value


def _optional_string(
    arguments: Mapping[str, Any], target: dict[str, Any], name: str, maximum: int
) -> None:
    if name in arguments:
        target[name] = _string(arguments[name], name, 1, maximum)


def _optional_enum(
    arguments: Mapping[str, Any],
    target: dict[str, Any],
    name: str,
    allowed: frozenset[str],
) -> None:
    if name in arguments:
        target[name] = _enum(arguments[name], name, allowed)


def _optional_integer(
    arguments: Mapping[str, Any],
    target: dict[str, Any],
    name: str,
    minimum: int,
    maximum: int,
) -> None:
    if name in arguments:
        value = arguments[name]
        if type(value) is not int or not minimum <= value <= maximum:
            raise ValidationError(
                f"{name} must be an integer from {minimum} to {maximum}"
            )
        target[name] = value


def _optional_boolean(
    arguments: Mapping[str, Any], target: dict[str, Any], name: str
) -> None:
    if name in arguments:
        if type(arguments[name]) is not bool:
            raise ValidationError(f"{name} must be a boolean")
        target[name] = arguments[name]


def _strings(
    value: object, name: str, maximum_items: int, maximum_length: int
) -> list[str]:
    if type(value) is not list or len(value) > maximum_items:
        raise ValidationError(f"{name} has too many items")
    return [_string(item, name, 1, maximum_length) for item in value]


def _array(value: object, name: str, maximum_items: int) -> list[Any]:
    if type(value) is not list or len(value) > maximum_items:
        raise ValidationError(f"{name} has too many items")
    _json_size(value, name, 16_384)
    _json_value(value, name)
    return value


def _object(value: object, name: str) -> dict[str, Any]:
    if type(value) is not dict or len(value) > 32:
        raise ValidationError(f"{name} must be an object with at most 32 keys")
    _json_size(value, name, 16_384)
    _json_value(value, name)
    return value


def _evidence(value: object) -> list[dict[str, Any]]:
    if type(value) is not list or len(value) > 32:
        raise ValidationError("evidence has too many items")
    result = []
    for item in value:
        if type(item) is not dict or set(item) - {"reference", "metadata"}:
            raise ValidationError("evidence item is invalid")
        result.append(
            {
                "reference": _string(item.get("reference"), "reference", 1, 2048),
                "metadata": _object(item.get("metadata", {}), "metadata"),
            }
        )
    return result


def _verifiers(value: object) -> list[dict[str, Any]]:
    if type(value) is not list or len(value) > 16:
        raise ValidationError("verifiers has too many items")
    result = []
    for item in value:
        if type(item) is not dict or set(item) - {
            "kind",
            "name",
            "status",
            "command",
            "artifact_uri",
            "metrics",
        }:
            raise ValidationError("verifier item is invalid")
        result.append(
            {
                "kind": _enum(item.get("kind"), "kind", _VERIFIER_KINDS),
                "name": _string(item.get("name"), "name", 1, 255),
                "status": _string(item.get("status"), "status", 1, 32),
                "command": _nullable_string(item.get("command"), "command", 2048),
                "artifact_uri": _nullable_string(
                    item.get("artifact_uri"), "artifact_uri", 2048
                ),
                "metrics": _object(item.get("metrics", {}), "metrics"),
            }
        )
    return result


def _json_size(value: object, name: str, maximum: int) -> None:
    try:
        size = len(json.dumps(value, allow_nan=False, separators=(",", ":")).encode())
    except (TypeError, ValueError) as error:
        raise ValidationError(f"{name} must be JSON-compatible") from error
    if size > maximum:
        raise ValidationError(f"{name} exceeds maximum size")


def _json_value(value: object, name: str, depth: int = 0) -> None:
    if depth > 4:
        raise ValidationError(f"{name} exceeds maximum nesting")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str or not 1 <= len(key) <= 128:
                raise ValidationError(f"{name} has invalid key")
            _json_value(item, name, depth + 1)
    elif type(value) is list:
        for item in value:
            _json_value(item, name, depth + 1)
    elif type(value) is float and not math.isfinite(value):
        raise ValidationError(f"{name} contains non-finite number")
    elif value is not None and type(value) not in {str, int, float, bool}:
        raise ValidationError(f"{name} must be JSON-compatible")
