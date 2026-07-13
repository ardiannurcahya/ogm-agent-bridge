# B4 conformance

## Covered

Lightweight tests use `httpx.MockTransport`; no core, Docker, or credentials.

- HTTP 400/401/403/404/413/415/422/500 mapping and failed-response closure.
- Retry count for retryable reads; one request for no-retry writes.
- Exact deep query response preservation.
- Project provenance/partition behavior in existing read, write, and state tests.
- Memory scope validation and omitted-option defaults.
- Upload UUID, approved-root, resolved-symlink escape, MIME fallback, multipart, and validation behavior.
- All seven MCP tool schemas and safe unexpected-error envelope.
- SQLite schema v3 migration, ambiguous write blocking, and safe finalization.

## Limits

Mock transport cannot prove OpenGraphMemory endpoint compatibility, authentication, database isolation, or multipart handling beyond bridge request shape. Harness stdio integration remains covered by adapter examples, not live harness processes.

## Optional real-core smoke

`tests/integration/test_real_core_smoke.py` skips unless `OGM_REAL_CORE_SMOKE=1`. It requires explicitly set `OGM_BASE_URL`, `OGM_API_KEY`, `OGM_PROJECT_ID`, and isolated non-default `OGM_STATE_DB`. Test starts no Docker and reads no credential files.
