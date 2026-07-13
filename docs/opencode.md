# OpenCode setup

## Install

1. Install OpenCode and `uv`.
2. Clone bridge and install locked dependencies:

   ```bash
   git clone <bridge-repository-url> /absolute/path/ogm-agent-bridge
   cd /absolute/path/ogm-agent-bridge
   uv sync
   ```

3. Export bridge variables before starting OpenCode:

   ```bash
   export OGM_BASE_URL="https://ogm.example.invalid"
   export OGM_API_KEY="replace-with-project-api-key"
   export OGM_PROJECT_ID="replace-with-project-uuid"
   export OGM_STATE_DB="/absolute/path/ogm-agent-bridge-state/state.db"
   export OGM_PERMISSION_PROFILE="read-only"
   ```

4. Copy `examples/opencode/opencode.json.example` to OpenCode config location or merge `mcp.ogm` into existing `opencode.json`. Replace every `/absolute/path/ogm-agent-bridge` with clone absolute path. Keep `{env:OGM_*}` values unchanged.
5. Restart OpenCode from shell where variables exist.

`/absolute/path/ogm-agent-bridge` is full clone path, not literal text or project-relative path. Example: `/home/alice/src/ogm-agent-bridge`.

Template uses documented OpenCode local-MCP form: `$schema`, `mcp`, `type: "local"`, command array, `environment` references, and `enabled`. No timeout: installed OpenCode unavailable for version check and current schema verification did not confirm timeout field.

## Trust and security

Local MCP process gets project API key through environment. Only add this config in trusted OpenCode scope. Do not commit literal secrets, copied personal config, or state database. Use project-scoped API key. Start `read-only`; set `personal-safe` only for planned writes.

## Verify

```bash
cd /absolute/path/ogm-agent-bridge
uv run --project /absolute/path/ogm-agent-bridge ogm-agent-bridge
```

Stop smoke process with `Ctrl-C`; stdio server waits for MCP client. Start OpenCode and inspect MCP connection/tool view. Expected 7 tools: `ogm_health`, `ogm_list_datasets`, `ogm_query`, `ogm_search_memory`, `ogm_create_session`, `ogm_remember`, `ogm_upload_document`. Call `ogm_health`, then `ogm_query` or `ogm_search_memory`.

## Troubleshoot

- `uv` missing: install uv or use absolute `uv` executable in command array.
- Missing config variable: export all five `OGM_*` values before OpenCode starts.
- Tools missing: check JSON syntax, `enabled: true`, absolute repo path, then restart OpenCode.
- API auth failure: check project key and project ID pair; do not put key in config.
- Write denied: `read-only` blocks write tools by design.
- SQLite failure: set `OGM_STATE_DB` to writable absolute path.
