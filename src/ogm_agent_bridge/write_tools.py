"""B2 write handlers."""

from __future__ import annotations

import mimetypes
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.errors import BridgeError, ValidationError
from ogm_agent_bridge.permissions import require_write
from ogm_agent_bridge.responses import envelope
from ogm_agent_bridge.state import StateStore
from ogm_agent_bridge.tools import _string


async def create_session(
    client: OGMClient, state: StateStore, profile: str, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    require_write(profile, "memory:write")
    user = _string(arguments, "user_external_id", 1, 255)
    agent = _string(arguments, "agent_name", 1, 255)
    old = state.session(user, agent)
    if old and old[2] == "active":
        return envelope(
            {"session_id": old[0], "core_session_id": old[1]},
            provenance={"project_id": client.project_id, "session_id": old[0]},
        )
    if old and old[2] == "uncertain":
        raise ValidationError(
            "Session identity uncertain; inspect core before retrying"
        )
    user_id = await _identity(
        client,
        state,
        "users",
        user,
        {
            "external_id": user,
            **_optional(arguments, "user_display_name", "display_name"),
        },
    )
    agent_id = await _identity(
        client,
        state,
        "agents",
        agent,
        {"name": agent, **_optional(arguments, "agent_description", "description")},
    )
    bridge_id = state.begin_session(user, agent)
    try:
        payload = {"user_id": user_id, "agent_id": agent_id}
        payload.update(_optional(arguments, "title", "title"))
        payload.update(_optional(arguments, "metadata", "metadata"))
        response = await client.request(
            "POST", "/v1/memory/sessions", json=payload, retry=False
        )
    except BridgeError as error:
        state.uncertain_session(bridge_id)
        raise ValidationError(
            "Session creation uncertain; inspect core before retrying"
        ) from error
    core_id = _id(response.json())
    state.finish_session(bridge_id, core_id)
    return envelope(
        {
            "session_id": bridge_id,
            "core_session_id": core_id,
            "user_id": user_id,
            "agent_id": agent_id,
        },
        provenance={"project_id": client.project_id, "session_id": bridge_id},
    )


async def _identity(
    client: OGMClient, state: StateStore, kind: str, key: str, payload: dict[str, Any]
) -> str:
    old = state.identity(kind, key)
    if old and old[1] == "active" and old[0]:
        return old[0]
    if old and old[1] == "uncertain":
        raise ValidationError("Identity uncertain; inspect core before retrying")
    state.begin_identity(kind, key)
    try:
        response = await client.request(
            "POST", f"/v1/memory/{kind}", json=payload, retry=False
        )
    except BridgeError as error:
        state.uncertain_identity(kind, key)
        raise ValidationError(
            "Identity creation uncertain; inspect core before retrying"
        ) from error
    core_id = _id(response.json())
    state.finish_identity(kind, key, core_id)
    return core_id


async def remember(
    client: OGMClient, state: StateStore, profile: str, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    require_write(profile, "memory:write")
    bridge_id = _string(arguments, "session_id", 1)
    core_id = state.resolve_session(bridge_id)
    if not core_id:
        raise ValidationError("Unknown or uncertain session")
    content = _string(arguments, "content", 1, 50_000)
    fact = {
        "subject": _string(arguments, "subject", 1, 255),
        "predicate": _string(arguments, "predicate", 1, 100),
        "value": _string(arguments, "value", 1, 5000),
    }
    payload = {
        "messages": [{"role": arguments.get("role", "user"), "content": content}],
        "facts": [fact],
    }
    response = await client.request(
        "POST", f"/v1/memory/sessions/{core_id}/messages", json=payload, retry=False
    )
    return envelope(
        response.json(),
        provenance={"project_id": client.project_id, "session_id": bridge_id},
    )


async def upload_document(
    client: OGMClient,
    profile: str,
    dataset_id: str,
    path: str,
    filename: str | None,
    mime_type: str | None,
) -> dict[str, Any]:
    require_write(profile, "documents:write")
    source = Path(path).expanduser()
    if not source.is_file():
        raise ValidationError("path must name a regular file")
    name = filename or source.name
    if not name:
        raise ValidationError("filename is invalid")
    mime = mime_type or mimetypes.guess_type(name)[0] or "application/octet-stream"
    with source.open("rb") as file:
        response = await client.request(
            "POST",
            f"/v1/datasets/{dataset_id}/documents",
            files={"file": (name, file, mime)},
            retry=False,
        )
    return envelope(
        response.json(),
        provenance={"project_id": client.project_id, "dataset_id": dataset_id},
    )


def _id(value: Any) -> str:
    if not isinstance(value, dict) or not isinstance(value.get("id"), str):
        raise ValidationError("Core response missing identity id")
    return cast(str, value["id"])


def _optional(arguments: Mapping[str, Any], source: str, target: str) -> dict[str, Any]:
    value = arguments.get(source)
    return {target: value} if value is not None else {}
