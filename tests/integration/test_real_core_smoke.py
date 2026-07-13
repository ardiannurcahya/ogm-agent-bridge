"""Optional real-core smoke test. Never starts Docker or reads credentials."""

from __future__ import annotations

import os

import httpx
import pytest

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.config import load_settings

pytestmark = pytest.mark.skipif(
    os.environ.get("OGM_REAL_CORE_SMOKE") != "1",
    reason="set OGM_REAL_CORE_SMOKE=1 with isolated real-core environment",
)


@pytest.mark.asyncio
async def test_real_core_health_requires_explicit_isolated_environment() -> None:
    required = ("OGM_BASE_URL", "OGM_API_KEY", "OGM_PROJECT_ID", "OGM_STATE_DB")
    assert all(os.environ.get(name) for name in required)
    assert os.environ["OGM_STATE_DB"] != os.path.expanduser(
        "~/.local/state/ogm-agent-bridge/state.db"
    )
    settings = load_settings()
    async with OGMClient(settings) as client:
        response = await client.request("GET", "/health", authenticated=False)
    assert response.status_code == httpx.codes.OK
