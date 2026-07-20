# Architecture

```text
Claude Code --|
OpenCode -----|-- MCP stdio -- graph and Agent Memory handlers -- authenticated HTTP -- OpenGraphMemory REST
Hermes -------|
```

Bridge is stateless. Each process has one core base URL, project API key, and project ID. Project calls send `X-API-Key` and `X-Project-Id`; health has no auth headers.

Handlers validate bounded tool input before calling graph and native Agent Memory REST routes. They return core data in a common envelope with known project/resource provenance. Stdout is MCP protocol only; diagnostics are redacted and sent to stderr.

`read-only` exposes graph and Agent Memory retrieval. `personal-safe` also permits validated local document uploads and additive memory records. `memory-curator` additionally permits feedback and supersession. Bridge has no destructive, admin, project creation, graph review, analytics refresh, direct backing-store, semantic retrieval-generation, or automatic conversation-ingestion calls.
