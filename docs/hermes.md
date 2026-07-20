# Hermes Setup

Install from PyPI with `uv tool install ogm-agent-bridge`, or run directly with `uvx ogm-agent-bridge`.

Merge `examples/hermes/config.yaml.example` under `mcp_servers`. Default example uses `uvx` and PyPI. For source development, replace command and args with `uv run --project /absolute/path/ogm-agent-bridge ogm-agent-bridge`.

Put `OGM_BASE_URL`, `OGM_API_KEY`, `OGM_PROJECT_ID`, and `OGM_PERMISSION_PROFILE` in local `~/.hermes/.env` with mode `0600`. Do not put keys in `config.yaml`.

Expected 21 tools: `mcp_ogm_ogm_health`, `mcp_ogm_ogm_list_datasets`, `mcp_ogm_ogm_search_entities`, `mcp_ogm_ogm_get_entity`, `mcp_ogm_ogm_get_neighbors`, `mcp_ogm_ogm_find_path`, `mcp_ogm_ogm_get_subgraph`, `mcp_ogm_ogm_get_graph`, `mcp_ogm_ogm_get_evidence`, `mcp_ogm_ogm_get_relation_evidence`, `mcp_ogm_ogm_upload_document`, `mcp_ogm_ogm_memory_list_episodes`, `mcp_ogm_ogm_memory_get_episode`, `mcp_ogm_ogm_memory_search`, `mcp_ogm_ogm_memory_create_episode`, `mcp_ogm_ogm_memory_append_attempt`, `mcp_ogm_ogm_memory_record_outcome`, `mcp_ogm_ogm_memory_feedback_episode`, `mcp_ogm_ogm_memory_supersede_episode`, `mcp_ogm_ogm_memory_feedback_pattern`, `mcp_ogm_ogm_memory_supersede_pattern`.

Run `hermes mcp test ogm`, then call health, datasets, and Agent Memory search. `read-only` blocks writes.
