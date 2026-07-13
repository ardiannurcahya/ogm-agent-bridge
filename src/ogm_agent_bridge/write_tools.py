"""B2 write handlers."""

from __future__ import annotations

import mimetypes
import os
import stat
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.errors import (
    AmbiguousWriteError,
    BridgeError,
    TimeoutError,
    TransportError,
    ValidationError,
)
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
    user_id = await _identity(
        client,
        state,
        "users",
        user,
        _payload(
            arguments,
            {
                "user_external_id": ("external_id", 1, 255),
                "user_display_name": ("display_name", 0, 255),
            },
            "user_metadata",
        ),
    )
    agent_id = await _identity(
        client,
        state,
        "agents",
        agent,
        _payload(
            arguments,
            {
                "agent_name": ("name", 1, 255),
                "agent_description": ("description", 0, 5000),
            },
            "agent_metadata",
        ),
    )
    bridge_id = state.begin_session(user, agent)
    payload = _payload(arguments, {"title": ("title", 0, 255)}, "session_metadata")
    payload.update({"user_id": user_id, "agent_id": agent_id})
    try:
        response = await client.request(
            "POST", "/v1/memory/sessions", json=payload, retry=False
        )
        core_id = _id(response.json())
    except (BridgeError, ValueError, TypeError, ValidationError) as error:
        state.uncertain_session(bridge_id)
        raise ValidationError(
            "Session creation uncertain; inspect core before retrying"
        ) from error
    try:
        state.finish_session(bridge_id, core_id)
    except Exception as error:
        try:
            state.uncertain_session(bridge_id)
        except Exception:
            pass
        raise BridgeError(
            "Session state uncertain; inspect local state before retrying"
        ) from error
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
    core_id, status = state.begin_identity(kind, key)
    if status == "active" and core_id:
        return core_id
    if status == "provisioning":
        raise ValidationError("Identity creation in progress; retry after repair")
    if status != "claimed":
        raise ValidationError("Identity uncertain; inspect core before retrying")
    try:
        response = await client.request(
            "POST", f"/v1/memory/{kind}", json=payload, retry=False
        )
        core_id = _id(response.json())
    except (BridgeError, ValueError, TypeError, ValidationError) as error:
        state.uncertain_identity(kind, key)
        raise ValidationError(
            "Identity creation uncertain; inspect core before retrying"
        ) from error
    try:
        state.finish_identity(kind, key, core_id)
    except Exception as error:
        try:
            state.uncertain_identity(kind, key)
        except Exception:
            pass
        raise BridgeError(
            "Identity state uncertain; inspect local state before retrying"
        ) from error
    return core_id


async def remember(
    client: OGMClient, state: StateStore, profile: str, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    require_write(profile, "memory:write")
    bridge_id = _string(arguments, "session_id", 1)
    core_id = state.resolve_session(bridge_id)
    if not core_id:
        raise ValidationError("Unknown or uncertain session")
    message = _object(arguments, "message")
    fact = _object(arguments, "fact")
    payload = {
        "messages": [_message(message)],
        "facts": [_fact(fact)],
    }
    try:
        response = await client.request(
            "POST",
            f"/v1/memory/sessions/{core_id}/messages",
            json=payload,
            retry=False,
            ambiguous_write=True,
        )
    except (AmbiguousWriteError, TimeoutError, TransportError) as error:
        try:
            state.block_session_writes(bridge_id)
        except Exception:
            pass
        raise BridgeError(
            "Message write uncertain; session blocked pending repair"
        ) from error
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
    upload_roots: tuple[Path, ...] | None = None,
) -> dict[str, Any]:
    require_write(profile, "documents:write")
    if not isinstance(dataset_id, str):
        raise ValidationError("dataset_id must be a UUID")
    try:
        uuid.UUID(dataset_id)
    except ValueError as error:
        raise ValidationError("dataset_id must be a UUID") from error
    if not isinstance(path, str) or not path:
        raise ValidationError("path must be a non-empty string")
    source = Path(path).expanduser().resolve()
    roots = upload_roots or (Path.cwd().resolve(),)
    if not any(source.is_relative_to(root) for root in roots):
        raise ValidationError("path must name a regular file")
    if filename is not None and (not isinstance(filename, str) or not filename):
        raise ValidationError("filename must be a non-empty string")
    if mime_type is not None and (not isinstance(mime_type, str) or not mime_type):
        raise ValidationError("mime_type must be a non-empty string")
    name = filename or source.name
    mime = mime_type or mimetypes.guess_type(name)[0] or "application/octet-stream"
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(source, flags)
    except OSError as error:
        raise ValidationError("path must name a regular file") from error
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValidationError("path must name a regular file")
        file = os.fdopen(fd, "rb")
    except Exception:
        os.close(fd)
        raise
    with file:
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


def _message(value: Mapping[str, Any]) -> dict[str, Any]:
    role = _string(value, "role", 1)
    if role not in {"system", "user", "assistant", "tool"}:
        raise ValidationError("role is invalid")
    payload: dict[str, Any] = {
        "role": role,
        "content": _string(value, "content", 1, 50_000),
    }
    return _with_metadata(payload, value)


def _fact(value: Mapping[str, Any]) -> dict[str, Any]:
    scope = value.get("scope", "user")
    if scope not in {"user", "agent", "session"}:
        raise ValidationError("scope is invalid")
    payload: dict[str, Any] = {
        "scope": scope,
        "subject": _string(value, "subject", 1, 255),
        "predicate": _string(value, "predicate", 1, 100),
        "value": _string(value, "value", 1, 5000),
    }
    if "confidence" in value:
        confidence = value["confidence"]
        if type(confidence) is not int or not 0 <= confidence <= 100:
            raise ValidationError("confidence must be an integer from 0 to 100")
        payload["confidence"] = confidence
    return _with_metadata(payload, value)


def _payload(
    arguments: Mapping[str, Any],
    strings: dict[str, tuple[str, int, int]],
    metadata: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        target: _string(arguments, source, minimum, maximum)
        for source, (target, minimum, maximum) in strings.items()
        if source in arguments
    }
    if metadata in arguments:
        payload["metadata"] = dict(_object(arguments, metadata))
    return payload


def _with_metadata(payload: dict[str, Any], value: Mapping[str, Any]) -> dict[str, Any]:
    if "metadata" in value:
        payload["metadata"] = dict(_object(value, "metadata"))
    return payload


def _object(arguments: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = arguments.get(name)
    if not isinstance(value, Mapping):
        raise ValidationError(f"{name} must be an object")
    return value


def _id(value: Any) -> str:
    if (
        not isinstance(value, dict)
        or not isinstance(value.get("id"), str)
        or not value["id"]
    ):
        raise ValidationError("Core response missing identity id")
    return cast(str, value["id"])
