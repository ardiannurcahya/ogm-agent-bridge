"""Safe document-upload handler."""

from __future__ import annotations

import mimetypes
import os
import stat
import uuid
from pathlib import Path
from typing import Any

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.errors import ValidationError
from ogm_agent_bridge.permissions import require_write
from ogm_agent_bridge.responses import envelope


async def upload_document(
    client: OGMClient,
    profile: str,
    dataset_id: str,
    path: str,
    filename: str | None,
    mime_type: str | None,
    upload_roots: tuple[Path, ...],
) -> dict[str, Any]:
    require_write(profile, "documents:write")
    try:
        uuid.UUID(dataset_id)
    except (TypeError, ValueError) as error:
        raise ValidationError("dataset_id must be a UUID") from error
    if not isinstance(path, str) or not path:
        raise ValidationError("path must be a non-empty string")
    source = Path(path).expanduser().resolve()
    if not any(source.is_relative_to(root) for root in upload_roots):
        raise ValidationError("path must name a regular file")
    if filename is not None and (not isinstance(filename, str) or not filename):
        raise ValidationError("filename must be a non-empty string")
    if mime_type is not None and (not isinstance(mime_type, str) or not mime_type):
        raise ValidationError("mime_type must be a non-empty string")
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
    name = filename or source.name
    mime = mime_type or mimetypes.guess_type(name)[0] or "application/octet-stream"
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
