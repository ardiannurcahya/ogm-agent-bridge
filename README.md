# ogm-agent-bridge

MCP stdio bridge from Claude Code, OpenCode, and Hermes to one OpenGraphMemory project.

Bridge uses authenticated OpenGraphMemory REST APIs only. It is stateless: no local database, session mapping, direct PostgreSQL, Neo4j, or object-store access.

## Status

Alpha. Source install is supported. PyPI publishing runs from GitHub Actions on `v*` tags.

## Tools

- `ogm_health`
- `ogm_list_datasets`
- `ogm_search_entities`
- `ogm_get_entity`
- `ogm_get_neighbors`
- `ogm_find_path`
- `ogm_get_subgraph`
- `ogm_get_graph`
- `ogm_get_evidence`
- `ogm_get_relation_evidence`
- `ogm_upload_document`

Read tools inspect PostgreSQL-authoritative graph data and evidence. `ogm_upload_document` is only write tool. No delete, update, admin, project-create, relation-review, analytics-refresh, memory, or semantic-retrieval tools exist.

## Setup

```bash
git clone https://github.com/ardiannurcahya/ogm-agent-bridge.git "$HOME/src/ogm-agent-bridge"
cd "$HOME/src/ogm-agent-bridge"
uv sync --locked
cp .env.example .env
```

Required configuration:

```env
OGM_BASE_URL=http://localhost:8000
OGM_API_KEY=<project-api-key>
OGM_PROJECT_ID=<project-uuid>
OGM_PERMISSION_PROFILE=read-only
```

Start server with `uv run ogm-agent-bridge`. MCP uses stdio; diagnostics use stderr.

## Agent Workflow

1. Call `ogm_health`.
2. Call `ogm_list_datasets`.
3. Call `ogm_search_entities` with selected dataset and term.
4. Use `ogm_get_neighbors`, `ogm_get_subgraph`, or `ogm_find_path` to inspect relationships.
5. Call `ogm_get_relation_evidence` or `ogm_get_evidence` before making evidence-backed claim.

Example `ogm_search_entities` arguments:

```json
{"dataset_id":"dataset-id","q":"OpenGraphMemory","limit":10}
```

## Harness Setup

- [Claude Code](docs/claude-code.md)
- [OpenCode](docs/opencode.md)
- [Hermes](docs/hermes.md)
- [Configuration](docs/configuration.md)
- [Tool schemas](docs/tools.md)

## Validation

```bash
uv sync --dev --locked
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest -q
uv build
```

## Security

Use project-scoped keys. Keep `.env` and keys outside upload roots. Start `read-only`; use `personal-safe` only for reviewed document uploads. See [security](docs/security.md).

## License

MIT. See [LICENSE](LICENSE).
