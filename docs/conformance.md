# B4 conformance

## Covered

Lightweight tests use `httpx.MockTransport`; no core, Docker, or credentials.

- HTTP 400/401/403/404/413/415/422/500 mapping and failed-response closure.
- Retry count for retryable reads; one request for no-retry writes.
- Exact deep query and graph/community response preservation.
- Query modes: `vector_only`, `graph_only`, `graph_local`, `graph_global`, `hybrid`; rejects `auto`.
- Query community fields: boolean `include_communities`, `community_level` 0..2.
- Exact graph explorer, community report, and report-job methods, paths, query params, and provenance.
- Project provenance/partition behavior in existing read, write, and state tests.
- Memory scope validation and omitted-option defaults.
- Upload UUID, approved-root, resolved-symlink escape, MIME fallback, multipart, `.json` `application/json`, raw JSON bytes, and validation behavior. Core validates malformed JSON.
- All eleven MCP tool schemas and safe unexpected-error envelope.
- SQLite schema v3 migration, ambiguous write blocking, and safe finalization.

## Limits

Mock transport cannot prove OpenGraphMemory endpoint compatibility, authentication, database isolation, or multipart handling beyond bridge request shape. Harness stdio integration remains covered by adapter examples, not live harness processes.

## Optional real-core smoke

`tests/integration/test_real_core_smoke.py` skips unless `OGM_REAL_CORE_SMOKE=1`. It requires explicitly set `OGM_BASE_URL`, `OGM_API_KEY`, `OGM_PROJECT_ID`, and isolated non-default `OGM_STATE_DB`. Test starts no Docker and reads no credential files.
