"""Safe document-upload handler."""

from __future__ import annotations

import mimetypes
import os
import re
import stat
import uuid
from pathlib import Path
from typing import Any, BinaryIO

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.errors import ValidationError
from ogm_agent_bridge.permissions import require_write
from ogm_agent_bridge.responses import envelope

_MAX_FILENAME_LENGTH = 255
_MAX_PATH_LENGTH = 4_096
_MAX_MIME_TYPE_LENGTH = 255
_MEDIA_TYPE = re.compile(r"[!#$&^_.+\-0-9A-Za-z]+/[!#$&^_.+\-0-9A-Za-z]+\Z")
_INVALID_FILE_PATH = "path must name a regular file"


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
    if not upload_roots:
        raise ValidationError("upload roots must be configured")
    if not isinstance(path, str) or not path or len(path) > _MAX_PATH_LENGTH:
        raise ValidationError("path must be a bounded non-empty string")
    components = _upload_path_components(path, upload_roots)
    name = filename if filename is not None else components[-1]
    _validate_filename(name)
    if mime_type is not None:
        _validate_mime_type(mime_type)
    file = _open_upload_source(components, upload_roots)
    mime = mime_type or mimetypes.guess_type(name)[0] or "application/octet-stream"
    with file:
        response = await client.request(
            "POST",
            f"/v1/datasets/{dataset_id}/documents",
            files={"file": (name, file, mime)},
            retry=False,
            ambiguous_write=True,
        )
    return envelope(
        response.json(),
        provenance={"project_id": client.project_id, "dataset_id": dataset_id},
    )


def _validate_upload_path(path: str) -> tuple[str, ...]:
    """Return safe relative path components without resolving caller input."""
    # pathlib otherwise raises platform-dependent exceptions for a NUL path.
    if "\x00" in path:
        raise ValidationError(_INVALID_FILE_PATH)
    try:
        candidate = Path(path)
        components = candidate.parts
    except (ValueError, OSError, RuntimeError) as error:
        raise ValidationError(_INVALID_FILE_PATH) from error
    if (
        candidate.is_absolute()
        or not components
        or any(len(component) > _MAX_FILENAME_LENGTH for component in components)
    ):
        raise ValidationError(_INVALID_FILE_PATH)
    if any(
        component in {"", ".", ".."} or "/" in component or "\\" in component
        for component in components
    ):
        raise ValidationError(_INVALID_FILE_PATH)
    return components


def _upload_path_components(
    path: str, upload_roots: tuple[Path, ...]
) -> tuple[str, ...]:
    """Convert a caller path to root-relative components without resolving it."""
    try:
        candidate = Path(path)
    except (ValueError, OSError, RuntimeError) as error:
        raise ValidationError(_INVALID_FILE_PATH) from error
    if not candidate.is_absolute():
        return _validate_upload_path(path)
    for root in upload_roots:
        try:
            relative = candidate.relative_to(root.resolve())
        except (ValueError, OSError, RuntimeError):
            continue
        return _validate_upload_path(str(relative))
    raise ValidationError(_INVALID_FILE_PATH)


def _open_upload_source(
    components: tuple[str, ...], upload_roots: tuple[Path, ...]
) -> BinaryIO:
    """Open a regular upload file below a root without path-based TOCTOU checks."""
    no_follow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if no_follow is None or directory is None:
        raise ValidationError(_INVALID_FILE_PATH)
    root_flags = os.O_RDONLY | no_follow | directory
    child_directory_flags = os.O_RDONLY | no_follow | directory
    file_flags = os.O_RDONLY | no_follow

    for root in upload_roots:
        current_fd: int | None = None
        file_fd: int | None = None
        try:
            # The root fd, rather than a resolved pathname, anchors every lookup.
            current_fd = os.open(root, root_flags)
            for component in components[:-1]:
                next_fd = os.open(component, child_directory_flags, dir_fd=current_fd)
                _close_fd(current_fd)
                current_fd = next_fd
            file_fd = os.open(components[-1], file_flags, dir_fd=current_fd)
            _close_fd(current_fd)
            current_fd = None
            if not stat.S_ISREG(os.fstat(file_fd).st_mode):
                raise ValidationError(_INVALID_FILE_PATH)
            file = os.fdopen(file_fd, "rb")
            file_fd = None  # os.fdopen now owns the descriptor.
            return file
        except ValidationError:
            raise
        except (ValueError, OSError, RuntimeError):
            # A root may simply not contain the requested relative file.
            continue
        finally:
            if file_fd is not None:
                _close_fd(file_fd)
            if current_fd is not None:
                _close_fd(current_fd)
    raise ValidationError(_INVALID_FILE_PATH)


def _close_fd(fd: int) -> None:
    """Close a descriptor while preserving the safe public validation error."""
    try:
        os.close(fd)
    except OSError:
        pass


def _validate_filename(filename: object) -> None:
    """Allow only a bounded single filename, never a path supplied by a caller."""
    if (
        not isinstance(filename, str)
        or not filename
        or len(filename) > _MAX_FILENAME_LENGTH
        or "/" in filename
        or "\\" in filename
        or filename in {".", ".."}
        or any(ord(character) < 32 or ord(character) == 127 for character in filename)
    ):
        raise ValidationError("filename must be a bounded basename")


def _validate_mime_type(mime_type: object) -> None:
    """Accept only a bounded type/subtype media type for multipart headers."""
    if (
        type(mime_type) is not str
        or not 1 <= len(mime_type) <= _MAX_MIME_TYPE_LENGTH
        or not _MEDIA_TYPE.fullmatch(mime_type)
    ):
        raise ValidationError("mime_type must be a bounded media type")
