import pytest

from ogm_agent_bridge.errors import (
    AuthenticationError,
    NotFoundError,
    PayloadTooLargeError,
    UnsupportedMediaError,
    UpstreamError,
    ValidationError,
    error_from_status,
)


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, AuthenticationError),
        (404, NotFoundError),
        (413, PayloadTooLargeError),
        (415, UnsupportedMediaError),
        (422, ValidationError),
        (500, UpstreamError),
    ],
)
def test_maps_http_status(status: int, expected: type[Exception]) -> None:
    assert isinstance(error_from_status(status), expected)
