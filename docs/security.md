# Security

Keep `OGM_API_KEY` in protected environment or `.env`; never commit keys, `.env`, logs, or copied MCP configs with secrets. Bridge sends project calls with `X-API-Key` and `X-Project-Id`; stdout remains MCP protocol.

Use `read-only` by default. `personal-safe` adds reviewed document upload plus additive Agent Memory records. `memory-curator` adds feedback and supersession; reserve it for reviewed governance actions. No delete, admin, project-create, relation-review, analytics, semantic-retrieval, or automatic conversation-ingestion tools are registered.

Upload reads local bytes and sends them to core. Set narrow `OGM_UPLOAD_ROOTS`, never `$HOME`, `/`, broad repository root, or shared temp directory. Review resolved path, filename, and content. Keep `.env`, SSH keys, browser data, and build secrets outside upload roots.

Agent Memory verifier commands and artifact URIs are stored as metadata only. The bridge never executes caller-provided commands, reads their artifact paths, or automatically captures conversations.
