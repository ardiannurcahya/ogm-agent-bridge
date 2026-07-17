# B4 conformance

## Covered

Lightweight tests use `httpx.MockTransport`; no core, Docker, or credentials.

- HTTP 400/401/403/404/413/415/422/500 mapping and failed-response closure.
- Retry count for retryable reads; one request for no-retry writes.
- Exact graph response preservation.
- Project provenance and graph route/query parameter behavior.
- Upload UUID, approved-root, resolved-symlink escape, MIME fallback, multipart, and validation behavior.
- All eleven MCP tool schemas and safe unexpected-error envelope.

## Limits

Mock transport cannot prove OpenGraphMemory endpoint compatibility, authentication, database isolation, or multipart handling beyond bridge request shape. Harness stdio integration remains covered by adapter examples, not live harness processes.

## Optional real-core smoke

`tests/integration/test_real_core_smoke.py` skips unless `OGM_REAL_CORE_SMOKE=1`. It requires explicitly set `OGM_BASE_URL`, `OGM_API_KEY`, and `OGM_PROJECT_ID`. Set `OGM_REAL_CORE_DATASET_ID` to run its graph-search smoke. Tests start no Docker and read no credential files.
