# OpenCode Setup

Install from PyPI with `uv tool install ogm-agent-bridge`, or run directly with `uvx ogm-agent-bridge`.

Merge `examples/opencode/opencode.json.example` into trusted OpenCode config. Default example uses `uvx` and PyPI. For source development, replace command with `uv run --project /absolute/path/ogm-agent-bridge ogm-agent-bridge`.

Export `OGM_BASE_URL`, `OGM_API_KEY`, `OGM_PROJECT_ID`, and `OGM_PERMISSION_PROFILE` before starting OpenCode. Keep `{env:OGM_*}` entries; do not commit keys.

Expected 21 tools: `ogm_health`, `ogm_list_datasets`, `ogm_search_entities`, `ogm_get_entity`, `ogm_get_neighbors`, `ogm_find_path`, `ogm_get_subgraph`, `ogm_get_graph`, `ogm_get_evidence`, `ogm_get_relation_evidence`, `ogm_upload_document`, `ogm_memory_list_episodes`, `ogm_memory_get_episode`, `ogm_memory_search`, `ogm_memory_create_episode`, `ogm_memory_append_attempt`, `ogm_memory_record_outcome`, `ogm_memory_feedback_episode`, `ogm_memory_supersede_episode`, `ogm_memory_feedback_pattern`, `ogm_memory_supersede_pattern`.

Restart OpenCode, then call `ogm_health`, `ogm_list_datasets`, and `ogm_memory_search`. Use `read-only` unless reviewed writes are needed.
