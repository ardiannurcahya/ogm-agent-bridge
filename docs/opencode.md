# OpenCode Setup

Clone bridge, run `uv sync --locked`, then merge `examples/opencode/opencode.json.example` into trusted OpenCode config. Replace `/absolute/path/ogm-agent-bridge` with clone path.

Export `OGM_BASE_URL`, `OGM_API_KEY`, `OGM_PROJECT_ID`, and `OGM_PERMISSION_PROFILE` before starting OpenCode. Keep `{env:OGM_*}` entries; do not commit keys.

Expected 11 tools: `ogm_health`, `ogm_list_datasets`, `ogm_search_entities`, `ogm_get_entity`, `ogm_get_neighbors`, `ogm_find_path`, `ogm_get_subgraph`, `ogm_get_graph`, `ogm_get_evidence`, `ogm_get_relation_evidence`, `ogm_upload_document`.

Restart OpenCode, then call `ogm_health` and `ogm_search_entities`. Use `read-only` unless reviewed uploads are needed.
