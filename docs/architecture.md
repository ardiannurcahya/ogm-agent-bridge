# Architecture

```text
Claude Code --|
OpenCode -----|-- MCP stdio -- graph tool handler -- authenticated HTTP -- OpenGraphMemory REST
Hermes -------|
```

Bridge is stateless. Each process has one core base URL, project API key, and project ID. Project calls send `X-API-Key` and `X-Project-Id`; health has no auth headers.

Handlers validate bounded tool input before calling current graph REST routes. They return core graph and evidence data in common envelope with known project/resource provenance. Stdout is MCP protocol only; diagnostics are redacted and sent to stderr.

`read-only` exposes all graph reads. `personal-safe` also permits validated local document uploads. Bridge has no destructive, admin, project creation, graph review, analytics refresh, direct backing-store, memory, or retrieval-generation calls.
