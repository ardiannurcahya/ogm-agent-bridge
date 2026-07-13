# Claude Code setup

## Install

1. Install `uv`.
2. Clone bridge and install locked dependencies:

   ```bash
   git clone <bridge-repository-url> /absolute/path/ogm-agent-bridge
   cd /absolute/path/ogm-agent-bridge
   uv sync
   ```

3. Export bridge variables in shell that starts Claude Code. Use absolute state-db path; `~` expansion is shell-only.

   ```bash
   export OGM_BASE_URL="https://ogm.example.invalid"
   export OGM_API_KEY="replace-with-project-api-key"
   export OGM_PROJECT_ID="replace-with-project-uuid"
   export OGM_STATE_DB="/absolute/path/ogm-agent-bridge-state/state.db"
   export OGM_PERMISSION_PROFILE="read-only"
   ```

4. Copy `examples/claude-code/.mcp.json.example` into trusted project as `.mcp.json`. Replace every `/absolute/path/ogm-agent-bridge` with clone absolute path. Keep `${OGM_*}` strings unchanged.
5. Restart Claude Code from shell where variables exist.

`/absolute/path/ogm-agent-bridge` means full filesystem path to clone, not literal path. Example: `/home/alice/src/ogm-agent-bridge`. Do not use repo-relative path: Claude starts MCP process from project context.

## Trust and security

Only add `.mcp.json` in trusted repository. `claude mcp list` can start project MCP servers while bypassing workspace trust dialog. `OGM_API_KEY` grants project API access. Do not commit `.mcp.json` with literal values, `.env`, or state database. Start with `read-only`; use `personal-safe` only when write tools needed.

## Verify

```bash
cd /absolute/path/ogm-agent-bridge
uv run --project /absolute/path/ogm-agent-bridge ogm-agent-bridge
```

Stop smoke process with `Ctrl-C`; stdio server waits for MCP client. Then open trusted project and run:

```bash
claude mcp list
claude mcp get ogm
```

Expected: server `ogm` and 7 tools: `ogm_health`, `ogm_list_datasets`, `ogm_query`, `ogm_search_memory`, `ogm_create_session`, `ogm_remember`, `ogm_upload_document`. Ask Claude Code to call `ogm_health`, then `ogm_query` or `ogm_search_memory`.

## Troubleshoot

- `uv: command not found`: install uv or replace `command` with absolute `uv` path.
- Config error or missing setting: export all five `OGM_*` variables before starting Claude Code.
- No tools: restart Claude Code after copying config; inspect `claude mcp get ogm`.
- Permission error: set `OGM_PERMISSION_PROFILE=personal-safe` only for intended write calls.
- State error: use writable absolute parent directory for `OGM_STATE_DB`.
