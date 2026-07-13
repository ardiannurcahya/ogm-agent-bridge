"""Safe bridge error taxonomy and HTTP status mapping."""

from __future__ import annotations


class BridgeError(Exception):
    """Base error safe for bridge callers."""

    status_code = 502
    code = "upstream_error"


class AuthenticationError(BridgeError):
    status_code = 401
    code = "authentication_error"


class PermissionError(BridgeError):
    status_code = 403
    code = "permission_denied"


class NotFoundError(BridgeError):
    status_code = 404
    code = "not_found"


class ValidationError(BridgeError):
    status_code = 400
    code = "validation_error"


class PayloadTooLargeError(BridgeError):
    status_code = 413
    code = "payload_too_large"


class UnsupportedMediaError(BridgeError):
    status_code = 415
    code = "unsupported_media"


class UpstreamError(BridgeError):
    status_code = 502
    code = "upstream_error"


class TimeoutError(BridgeError):
    status_code = 504
    code = "timeout"


class TransportError(BridgeError):
    status_code = 503
    code = "transport_error"


def error_from_status(status_code: int, message: str = "Request failed") -> BridgeError:
    """Map upstream HTTP status to public error type."""
    mapping: dict[int, type[BridgeError]] = {
        401: AuthenticationError,
        403: PermissionError,
        404: NotFoundError,
        413: PayloadTooLargeError,
        415: UnsupportedMediaError,
    }
    if status_code == 400 or 422 <= status_code < 500:
        return ValidationError(message)
    return mapping.get(status_code, UpstreamError)(message)
