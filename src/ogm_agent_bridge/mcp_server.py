"""Graph-first stdio MCP server."""

from __future__ import annotations

import sys
from collections.abc import Awaitable, Callable
from typing import Any

from mcp.server.fastmcp import FastMCP

from ogm_agent_bridge import __version__
from ogm_agent_bridge.agent_memory_tools import (
    append_attempt,
    create_episode,
    feedback_episode,
    feedback_pattern,
    list_episodes,
    record_outcome,
    supersede_episode,
    supersede_pattern,
)
from ogm_agent_bridge.agent_memory_tools import (
    get_episode as get_memory_episode,
)
from ogm_agent_bridge.agent_memory_tools import (
    search as search_memory,
)
from ogm_agent_bridge.client import OGMClient
from ogm_agent_bridge.config import Settings, load_settings
from ogm_agent_bridge.errors import BridgeError
from ogm_agent_bridge.permissions import require_read
from ogm_agent_bridge.responses import envelope, safe_error
from ogm_agent_bridge.tools import (
    find_path,
    get_entity,
    get_evidence,
    get_graph,
    get_neighbors,
    get_relation_evidence,
    get_subgraph,
    list_datasets,
    search_entities,
)


async def health(client: OGMClient) -> dict[str, Any]:
    require_read("health")
    response = await client.request("GET", "/health", authenticated=False)
    return envelope(response.json())


def create_server(settings: Settings | None = None) -> FastMCP:
    resolved_settings = settings or load_settings()
    server = FastMCP("ogm-agent-bridge")

    @server.tool(description="Check OpenGraphMemory core liveness.")
    async def ogm_health() -> dict[str, Any]:
        return await _call(resolved_settings, health)

    @server.tool(description="List datasets visible in configured project.")
    async def ogm_list_datasets() -> dict[str, Any]:
        return await _call(resolved_settings, list_datasets)

    @server.tool(description="Search supported graph entities in a dataset.")
    async def ogm_search_entities(
        dataset_id: str,
        q: str,
        entity_type: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            search_entities,
            _defined(dataset_id=dataset_id, q=q, entity_type=entity_type, limit=limit),
        )

    @server.tool(description="Read one graph entity by ID.")
    async def ogm_get_entity(entity_id: str) -> dict[str, Any]:
        return await _call(resolved_settings, get_entity, entity_id)

    @server.tool(description="Read bounded graph neighbors for one entity.")
    async def ogm_get_neighbors(
        entity_id: str, limit: int | None = None
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings, get_neighbors, _defined(entity_id=entity_id, limit=limit)
        )

    @server.tool(description="Find bounded graph path between two dataset entities.")
    async def ogm_find_path(
        dataset_id: str,
        source_entity_id: str,
        target_entity_id: str,
        max_depth: int | None = None,
        relation_limit: int | None = None,
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            find_path,
            _defined(
                dataset_id=dataset_id,
                source_entity_id=source_entity_id,
                target_entity_id=target_entity_id,
                max_depth=max_depth,
                relation_limit=relation_limit,
            ),
        )

    @server.tool(description="Read bounded graph subgraph around one entity.")
    async def ogm_get_subgraph(
        dataset_id: str,
        entity_id: str,
        depth: int | None = None,
        node_limit: int | None = None,
        relation_limit: int | None = None,
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            get_subgraph,
            _defined(
                dataset_id=dataset_id,
                entity_id=entity_id,
                depth=depth,
                node_limit=node_limit,
                relation_limit=relation_limit,
            ),
        )

    @server.tool(description="Read bounded dataset graph summary.")
    async def ogm_get_graph(
        dataset_id: str, limit: int | None = None, depth: int | None = None
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            get_graph,
            _defined(dataset_id=dataset_id, limit=limit, depth=depth),
        )

    @server.tool(description="Read graph evidence by ID.")
    async def ogm_get_evidence(evidence_id: str) -> dict[str, Any]:
        return await _call(resolved_settings, get_evidence, evidence_id)

    @server.tool(description="Read bounded evidence supporting one dataset relation.")
    async def ogm_get_relation_evidence(
        dataset_id: str, relation_id: str, limit: int | None = None
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            get_relation_evidence,
            _defined(dataset_id=dataset_id, relation_id=relation_id, limit=limit),
        )

    @server.tool(description="Upload regular local file to configured project dataset.")
    async def ogm_upload_document(
        dataset_id: str,
        path: str,
        filename: str | None = None,
        mime_type: str | None = None,
    ) -> dict[str, Any]:
        try:
            from ogm_agent_bridge.write_tools import upload_document

            async with OGMClient(resolved_settings) as client:
                return await upload_document(
                    client,
                    resolved_settings.permission_profile,
                    dataset_id,
                    path,
                    filename,
                    mime_type,
                    resolved_settings.upload_roots,
                )
        except Exception as error:
            return _tool_error(error)

    @server.tool(description="List project-scoped Agent Memory episodes.")
    async def ogm_memory_list_episodes(
        status: str | None = None, limit: int | None = None
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            list_episodes,
            _defined(status=status, limit=limit),
        )

    @server.tool(description="Read one project-scoped Agent Memory episode.")
    async def ogm_memory_get_episode(episode_id: str) -> dict[str, Any]:
        return await _call(resolved_settings, get_memory_episode, episode_id)

    @server.tool(description="Search verified and historical Agent Memory episodes.")
    async def ogm_memory_search(
        q: str,
        problem_signature: str | None = None,
        repository: str | None = None,
        environment: str | None = None,
        include_inactive: bool | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            search_memory,
            _defined(
                q=q,
                problem_signature=problem_signature,
                repository=repository,
                environment=environment,
                include_inactive=include_inactive,
                limit=limit,
            ),
        )

    @server.tool(description="Create a project-scoped Agent Memory episode.")
    async def ogm_memory_create_episode(
        domain: str,
        title: str,
        goal: str,
        problem_signature: str,
        scope: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        evidence: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            create_episode,
            resolved_settings.permission_profile,
            _defined(
                domain=domain,
                title=title,
                goal=goal,
                problem_signature=problem_signature,
                scope=scope,
                tags=tags,
                metadata=metadata,
                evidence=evidence,
            ),
        )

    @server.tool(description="Append a bounded attempt to an Agent Memory episode.")
    async def ogm_memory_append_attempt(
        episode_id: str,
        hypothesis: str,
        result: str,
        actions: list[Any] | None = None,
        notes: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            append_attempt,
            resolved_settings.permission_profile,
            episode_id,
            _defined(
                hypothesis=hypothesis,
                result=result,
                actions=actions,
                notes=notes,
                metadata=metadata,
            ),
        )

    @server.tool(description="Record a final Agent Memory outcome with verifiers.")
    async def ogm_memory_record_outcome(
        episode_id: str,
        status: str,
        summary: str,
        lesson: str | None = None,
        verifiers: list[dict[str, Any]] | None = None,
        metrics: dict[str, Any] | None = None,
        pattern_key: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            record_outcome,
            resolved_settings.permission_profile,
            episode_id,
            _defined(
                status=status,
                summary=summary,
                lesson=lesson,
                verifiers=verifiers,
                metrics=metrics,
                pattern_key=pattern_key,
                metadata=metadata,
            ),
        )

    @server.tool(description="Curate confidence feedback for an Agent Memory episode.")
    async def ogm_memory_feedback_episode(
        episode_id: str, score: int
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            feedback_episode,
            resolved_settings.permission_profile,
            episode_id,
            score,
        )

    @server.tool(
        description="Mark an Agent Memory episode superseded by another episode."
    )
    async def ogm_memory_supersede_episode(
        episode_id: str, superseding_episode_id: str
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            supersede_episode,
            resolved_settings.permission_profile,
            episode_id,
            superseding_episode_id,
        )

    @server.tool(description="Curate confidence feedback for an Agent Memory pattern.")
    async def ogm_memory_feedback_pattern(
        pattern_key: str, score: int
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            feedback_pattern,
            resolved_settings.permission_profile,
            pattern_key,
            score,
        )

    @server.tool(
        description="Mark an Agent Memory pattern superseded by another pattern."
    )
    async def ogm_memory_supersede_pattern(
        pattern_key: str, superseding_pattern_key: str
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            supersede_pattern,
            resolved_settings.permission_profile,
            pattern_key,
            superseding_pattern_key,
        )

    return server


async def _call(
    settings: Settings,
    handler: Callable[..., Awaitable[dict[str, Any]]],
    *arguments: Any,
) -> dict[str, Any]:
    try:
        async with OGMClient(settings) as client:
            return await handler(client, *arguments)
    except Exception as error:
        return _tool_error(error)


def _defined(**values: Any) -> dict[str, Any]:
    return {name: value for name, value in values.items() if value is not None}


def _tool_error(error: Exception) -> dict[str, Any]:
    if isinstance(error, BridgeError):
        return safe_error(error)
    print("ogm-agent-bridge: internal tool failure", file=sys.stderr)
    return safe_error(BridgeError("Internal bridge error"))


def main() -> None:
    if "--version" in sys.argv[1:]:
        print(__version__)
        return
    create_server().run(transport="stdio")
