# Plan

## Goal & scope

Make OpenGraphMemory usable from Claude Code, OpenCode, Hermes through MCP. Ship one thin, project-scoped stdio bridge over core REST.

## Key decisions

1. Core REST only. No direct database, vector, graph, or object-store access.
2. One MCP server serves all harnesses.
3. Stdio transport first.
4. One bridge instance maps to one core project.
5. Core auth uses `X-API-Key` plus `X-Project-Id`.
6. Keep seven 0.1.0 tools: health, list datasets, query, search memory, create session, remember, upload document.
7. Reads and personal-safe writes ship; destructive tools do not.
8. MCP output uses common envelope with provenance and warnings.
9. Bridge owns SQLite session mapping and provisioned identity state; core lacks session/message list endpoints.
10. `create_session` auto-provisions user and agent; `remember` writes facts through message batch.
11. Search memory is lexical; preserve core citations and do not overstate recall quality.

## Milestones

### B0 — Foundation

Deliverables:

- Repo scaffold and `pyproject.toml` using uv.
- Config loader from environment and `.env`.
- Async HTTP client with dual-header auth, timeout, bounded retry.
- Error taxonomy and safe error mapper.
- Structured stderr logging, secret redaction.
- CI: ruff, mypy, pytest.

Exit criteria:

- `uv run` imports package and loads validated config.
- Client sends both auth headers on project calls.
- Tests prove API key redaction and error mapping.
- CI passes ruff, mypy, pytest.

### B1 — MCP read tools

Deliverables:

- Stdio MCP server.
- `ogm_health`, `ogm_list_datasets`, `ogm_query`, `ogm_search_memory`.
- Common response envelope and read permission checks.

Exit criteria:

- MCP Inspector completes `initialize`, `tools/list`, `tools/call`.
- Inspector calls all four read tools against mock core.
- Query preserves citations and retrieval trace.

### B2 — Session + write tools

Deliverables:

- SQLite state store.
- Resolve identity recovery prerequisite: add/verify core user-agent lookup/upsert endpoints, or define and test SQLite backup/restore as an explicit compatibility limitation.
- `ogm_create_session` with auto-provision user/agent.
- `ogm_remember`, `ogm_upload_document`.
- Hardcoded personal-safe permission allowlist.

Exit criteria:

- End-to-end: create session → remember → query with `memory_*` works.
- SQLite restores mapping after bridge restart.
- Identity provisioning remains idempotent after normal restart; state-loss behavior is documented and tested.
- Disallowed destructive operation has no registered tool/call path.

### B3 — Harness adapters

Deliverables:

- Claude Code `.mcp.json` example.
- OpenCode config example.
- Hermes skill plus wrapper.
- Install docs for each harness.

Exit criteria:

- Claude Code, OpenCode, Hermes each call `ogm_query` and `ogm_search_memory`.
- Examples use environment variables, never committed secrets.

### B4 — Contract tests + conformance

Deliverables:

- Unit tests: config, redaction, permissions.
- Contract tests against mock core API.
- Optional integration suite against real core container.
- Conformance scenarios: auth error, unknown project, citation preserved, memory scope, remember needs permission, duplicate document, timeout mapping.

Exit criteria:

- Contract suite asserts methods, paths, headers, request fields, constraints, response mapping.
- Every listed scenario passes.
- Real-core suite runs when integration environment enabled.

### B5 — Packaging

Deliverables:

- `pyproject.toml` console entry point, runnable through `uvx`.
- Versioning policy and dependency pins.
- Release/install docs.

Exit criteria:

- Clean machine command runs bridge with `uvx`.
- Version appears in package and release docs.
- Install docs work for all three harnesses.

## Deferred to later versions

0.2+: cross-harness session sync; automatic conversation ingestion with secret filtering; manifest generator; full permission-policy engine; OpenClaw plugin; destructive tools; HTTP MCP transport.

## Proposed repo structure

```text
src/ogm_agent_bridge/
├── __init__.py
├── config.py
├── errors.py
├── logging.py
├── client.py
├── state.py
├── permissions.py
├── mcp_server.py
└── tools/
    ├── health.py
    ├── datasets.py
    ├── query.py
    ├── memory.py
    └── documents.py
adapters/
├── claude-code/
├── opencode/
└── hermes/
tests/
├── unit/
├── contract/
├── integration/
└── conformance/
docs/
```

## First implementation steps

1. Create uv `pyproject.toml`, `src` package, test layout, ruff/mypy/pytest config.
2. Add typed config. Require base URL, API key, project ID; load `.env`; set timeout/retry/state defaults.
3. Add stderr structured logger and recursive secret redactor. Test no key leaks.
4. Add error classes: auth, not-found, validation, payload-too-large, unsupported-media, upstream, timeout, transport, permission.
5. Build async `httpx` client. Normalize base URL. Send both headers. Set timeout. Retry only retryable failures.
6. Build contract-test mock core. Assert route, headers, payload, mapped errors.
7. Add minimal stdio MCP server and common result/error envelope.
8. Implement B1 in tool order: health, datasets, query, search memory.
9. Run MCP Inspector exit flow before B2.
10. Add SQLite migrations/store, then B2 tools and permission allowlist.
