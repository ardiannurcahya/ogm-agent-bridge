# Hermes setup

Verified against installed Hermes Agent v0.14.0 source.

## Install

1. Install Hermes, `uv`, then bridge:

   ```bash
   git clone <bridge-repository-url> /absolute/path/ogm-agent-bridge
   cd /absolute/path/ogm-agent-bridge
   uv sync
   ```

2. Add bridge variables to local-only `~/.hermes/.env` with mode `0600`:

   ```bash
   install -m 600 /dev/null ~/.hermes/.env
   ```

   Add these values. Do not put them in `config.yaml`.

   ```env
   OGM_BASE_URL=https://ogm.example.invalid
   OGM_API_KEY=replace-with-project-api-key
   OGM_PROJECT_ID=replace-with-project-uuid
   OGM_STATE_DB=/absolute/path/ogm-agent-bridge-state/state.db
   OGM_PERMISSION_PROFILE=read-only
   ```

3. Merge `examples/hermes/config.yaml.example` under `mcp_servers` in `~/.hermes/config.yaml`. Replace every `/absolute/path/ogm-agent-bridge` with clone full path. Keep `${OGM_*}` strings unchanged.
4. Restart Hermes.

`/absolute/path/ogm-agent-bridge` is full filesystem clone path, not literal text. Example: `/home/alice/src/ogm-agent-bridge`. Template uses `uv` from `PATH`, not machine-specific `/root/.local/bin/uv`. If uv is absent from Hermes PATH, replace `command: "uv"` with local uv absolute path.

## Why this env form

Hermes loads `~/.hermes/.env` into process environment, then expands `${VAR}` recursively in `config.yaml`. Its MCP subprocess environment is filtered: `OGM_*` values do **not** pass unless explicit under server `env`. This template explicitly passes five bridge-required values. Hermes leaves unresolved `${VAR}` literal, so missing `.env` entries fail bridge config instead of silently using host values. `timeout: 120` and `connect_timeout: 60` are Hermes documented seconds/defaults.

## Trust and security

Hermes starts MCP subprocesses and discovers tools at startup. Only add trusted local bridge path. `~/.hermes/.env` contains secret; do not commit, paste into `config.yaml`, logs, screenshots, or shell history. Use restrictive permissions. Project API key grants API access. Start `read-only`; use `personal-safe` only for intended write tools.

## Verify

```bash
cd /absolute/path/ogm-agent-bridge
uv run --project /absolute/path/ogm-agent-bridge ogm-agent-bridge
```

Stop smoke process with `Ctrl-C`; stdio server waits for MCP client. Then run:

```bash
hermes mcp list
hermes mcp test ogm
hermes tools list
```

Expected 7 tools after startup: `mcp_ogm_ogm_health`, `mcp_ogm_ogm_list_datasets`, `mcp_ogm_ogm_query`, `mcp_ogm_ogm_search_memory`, `mcp_ogm_ogm_create_session`, `mcp_ogm_ogm_remember`, `mcp_ogm_ogm_upload_document`. Ask Hermes to call `mcp_ogm_ogm_health`, then `mcp_ogm_ogm_query` or `mcp_ogm_ogm_search_memory`.

## Troubleshoot

- `Failed to connect`: check `command`, `args`, absolute clone path, then `hermes mcp test ogm`.
- Bridge says config missing: check all five `OGM_*` entries in `~/.hermes/.env`; restart Hermes after edit.
- Tools missing: inspect `hermes mcp list`, `hermes mcp test ogm`, then `hermes tools list`; MCP tools have `mcp_ogm_` prefix.
- Timeout: increase `connect_timeout` for discovery or `timeout` for calls in local config.
- Write denied: `read-only` blocks write tools. Change only after reviewing write scope.
- State failure: use writable absolute `OGM_STATE_DB` parent directory.
