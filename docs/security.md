# Security

Keep `OGM_API_KEY` in protected environment or `.env`; never commit keys, `.env`, logs, or copied MCP configs with secrets. Bridge sends project calls with `X-API-Key` and `X-Project-Id`; stdout remains MCP protocol.

Use `read-only` by default. `personal-safe` adds only `ogm_upload_document`. No delete, update, admin, project-create, relation-review, or analytics tools are registered.

Upload reads local bytes and sends them to core. Set narrow `OGM_UPLOAD_ROOTS`, never `$HOME`, `/`, broad repository root, or shared temp directory. Review resolved path, filename, and content. Keep `.env`, SSH keys, browser data, and build secrets outside upload roots.
