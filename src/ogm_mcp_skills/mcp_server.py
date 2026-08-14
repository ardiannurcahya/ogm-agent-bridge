"""Graph-first stdio MCP server."""

from __future__ import annotations

import sys
from collections.abc import Awaitable, Callable
from typing import Any

from mcp.server.fastmcp import FastMCP

from ogm_mcp_skills import __version__
from ogm_mcp_skills.agent_memory_tools import (
    append_attempt,
    create_episode,
    feedback_episode,
    feedback_pattern,
    list_episodes,
    record_outcome,
    supersede_episode,
    supersede_pattern,
)
from ogm_mcp_skills.agent_memory_tools import (
    get_episode as get_memory_episode,
)
from ogm_mcp_skills.agent_memory_tools import (
    search as search_memory,
)
from ogm_mcp_skills.client import OGMClient
from ogm_mcp_skills.codebase_tools import (
    get_code_call_graph,
    get_code_chunks,
    index_codebase,
    recall_code_memory,
    record_code_fix,
    search_code_symbols,
    sync_code_file,
)
from ogm_mcp_skills.config import Settings, load_settings
from ogm_mcp_skills.errors import BridgeError
from ogm_mcp_skills.permissions import require_read
from ogm_mcp_skills.responses import envelope, safe_error
from ogm_mcp_skills.tools import (
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
    server = FastMCP("ogm-mcp-skills")

    @server.tool(description="Check OpenGraphMemory core liveness.")
    async def ogm_health() -> dict[str, Any]:
        return await _call(resolved_settings, health)

    @server.tool(description="List datasets visible in configured project.")
    async def ogm_list_datasets() -> dict[str, Any]:
        return await _call(resolved_settings, list_datasets)

    @server.tool(description="Search graph entities by keyword in a dataset.")
    async def ogm_search_entities(
        dataset_id: str,
        q: str | None = None,
        query: str | None = None,
        entity_type: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            search_entities,
            _defined(
                dataset_id=dataset_id,
                q=q,
                query=query,
                entity_type=entity_type,
                limit=limit,
            ),
        )

    @server.tool(description="Read one graph entity by ID.")
    async def ogm_get_entity(entity_id: str) -> dict[str, Any]:
        return await _call(resolved_settings, get_entity, entity_id)

    @server.tool(description="Read bounded graph neighbors for one entity.")
    async def ogm_get_neighbors(
        entity_id: str | None = None,
        symbol_id: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            get_neighbors,
            _defined(entity_id=entity_id, symbol_id=symbol_id, limit=limit),
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
        entity_id: str | None = None,
        root_entity_id: str | None = None,
        symbol_id: str | None = None,
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
                root_entity_id=root_entity_id,
                symbol_id=symbol_id,
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
            from ogm_mcp_skills.write_tools import upload_document

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

    # --- Codebase Knowledge Graph & Codebase Memory Tools ---

    @server.tool(
        description="Search codebase symbols (functions, classes, interfaces, structs) in a dataset."
    )
    async def ogm_search_code_symbols(
        dataset_id: str,
        q: str | None = None,
        query: str | None = None,
        kind: str | None = None,
        language: str | None = None,
        file_path: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            search_code_symbols,
            _defined(
                dataset_id=dataset_id,
                q=q,
                query=query,
                kind=kind,
                language=language,
                file_path=file_path,
                limit=limit,
            ),
        )

    @server.tool(
        description="Inspect callers, calls, and inheritance for a code symbol."
    )
    async def ogm_get_code_call_graph(
        entity_id: str | None = None,
        symbol_id: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            get_code_call_graph,
            _defined(entity_id=entity_id, symbol_id=symbol_id, limit=limit),
        )

    @server.tool(
        description="Fetch codebase nodes, degree centrality rankings, and AST structural chunks for a dataset."
    )
    async def ogm_get_code_chunks(
        dataset_id: str, file_path: str | None = None, limit: int | None = None
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            get_code_chunks,
            _defined(dataset_id=dataset_id, file_path=file_path, limit=limit),
        )

    @server.tool(
        description="Recall past agent bugfixes and refactoring memories for a file or function."
    )
    async def ogm_recall_code_memory(
        file_path: str | None = None,
        function_name: str | None = None,
        q: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            recall_code_memory,
            _defined(
                file_path=file_path,
                function_name=function_name,
                q=q,
                limit=limit,
            ),
        )

    @server.tool(
        description="Record an agent memory episode for a codebase bug fix or refactor."
    )
    async def ogm_record_code_fix(
        file_path: str,
        title: str,
        goal: str,
        root_cause: str,
        solution: str,
        function_name: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            record_code_fix,
            resolved_settings.permission_profile,
            _defined(
                file_path=file_path,
                title=title,
                goal=goal,
                root_cause=root_cause,
                solution=solution,
                function_name=function_name,
                idempotency_key=idempotency_key,
            ),
        )

    @server.tool(
        description="Sync a single edited code file into the Knowledge Graph in real-time."
    )
    async def ogm_sync_code_file(
        dataset_id: str,
        file_path: str,
        code: str,
        language: str | None = None,
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            sync_code_file,
            resolved_settings.permission_profile,
            _defined(
                dataset_id=dataset_id,
                file_path=file_path,
                code=code,
                language=language,
            ),
        )

    @server.tool(
        description="Scan and extract an entire local codebase repository (directory) into an isolated OpenGraphMemory dataset in seconds with full AST call graphs."
    )
    async def ogm_index_codebase(
        path: str | None = None,
        directory_path: str | None = None,
        dataset_id: str | None = None,
        dataset_name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        return await _call(
            resolved_settings,
            index_codebase,
            resolved_settings.permission_profile,
            _defined(
                path=path,
                directory_path=directory_path,
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                description=description,
            ),
        )

    # FastMCP derives schemas from signatures; forbid argument smuggling on every
    # public tool in addition to handler-level validation.
    for tool in server._tool_manager._tools.values():
        tool.parameters["additionalProperties"] = False
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
    print("ogm-mcp-skills: internal tool failure", file=sys.stderr)
    return safe_error(BridgeError("Internal bridge error"))


def main() -> None:
    if "--version" in sys.argv[1:]:
        print(__version__)
        return
    create_server().run(transport="stdio")
