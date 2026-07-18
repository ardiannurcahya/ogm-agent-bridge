# Claude Code Setup

Install from PyPI with `uv tool install ogm-agent-bridge`, or run directly with `uvx ogm-agent-bridge`.

Copy `examples/claude-code/.mcp.json.example` to trusted project `.mcp.json`. Default example uses `uvx` and PyPI. For source development, replace command and args with `uv run --project /absolute/path/ogm-agent-bridge ogm-agent-bridge`.

Export `OGM_BASE_URL`, `OGM_API_KEY`, `OGM_PROJECT_ID`, and `OGM_PERMISSION_PROFILE` before starting Claude Code. Do not put literal keys in `.mcp.json`.

Expected 11 tools: `ogm_health`, `ogm_list_datasets`, `ogm_search_entities`, `ogm_get_entity`, `ogm_get_neighbors`, `ogm_find_path`, `ogm_get_subgraph`, `ogm_get_graph`, `ogm_get_evidence`, `ogm_get_relation_evidence`, `ogm_upload_document`.

Verify with `claude mcp list`, then call `ogm_health`, `ogm_list_datasets`, and `ogm_search_entities`. `read-only` blocks upload.
