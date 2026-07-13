"""B1 read-tool handlers."""

from __future__ import annotations

from typing import Any

from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.permissions import require_read
from ogm_agent_bridge.responses import envelope


async def list_datasets(client: OGMClient) -> dict[str, Any]:
    """List datasets in configured project."""
    require_read("datasets:read")
    response = await client.request("GET", "/v1/datasets")
    return envelope(response.json(), provenance={"project_id": client.project_id})
