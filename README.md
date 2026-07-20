# ogm-agent-bridge

MCP stdio bridge from Claude Code, OpenCode, and Hermes to one OpenGraphMemory project.

Bridge uses authenticated OpenGraphMemory REST APIs only. It is stateless: no local database, session mapping, direct PostgreSQL, Neo4j, or object-store access.

## Status

Alpha. PyPI releases are published from GitHub Actions on `v*` tags. Source install is also supported for development.

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
- `ogm_memory_list_episodes`
- `ogm_memory_get_episode`
- `ogm_memory_search`
- `ogm_memory_create_episode`
- `ogm_memory_append_attempt`
- `ogm_memory_record_outcome`
- `ogm_memory_feedback_episode`
- `ogm_memory_supersede_episode`
- `ogm_memory_feedback_pattern`
- `ogm_memory_supersede_pattern`

Read tools inspect PostgreSQL-authoritative graph and Agent Memory data. Agent Memory results are historical claims: inspect recorded evidence and verifiers before relying on them. `personal-safe` permits reviewed document upload and additive Agent Memory records; `memory-curator` additionally permits memory feedback and supersession. No delete, admin, project-create, relation-review, analytics-refresh, semantic-retrieval, or automatic conversation-ingestion tools exist.

## Install

Install from PyPI with `uv`:

```bash
uv tool install ogm-agent-bridge
```

Or run without installing:

```bash
uvx ogm-agent-bridge --version
```

`pipx` also works:

```bash
pipx install ogm-agent-bridge
```

For source development:

```bash
git clone https://github.com/ardiannurcahya/ogm-agent-bridge.git "$HOME/src/ogm-agent-bridge"
cd "$HOME/src/ogm-agent-bridge"
uv sync --locked
```

## Configure

Set these environment variables before starting your MCP client:

```env
OGM_BASE_URL=http://localhost:8000
OGM_API_KEY=<project-api-key>
OGM_PROJECT_ID=<project-uuid>
OGM_PERMISSION_PROFILE=read-only
```

Use `OGM_PERMISSION_PROFILE=read-only` for graph and Agent Memory retrieval. Use `OGM_PERMISSION_PROFILE=personal-safe` for reviewed uploads and additive Agent Memory records. Use `memory-curator` only for reviewed feedback and supersession.

Optional upload roots:

```env
OGM_UPLOAD_ROOTS=/absolute/path/to/allowed/docs
```

More options: [Configuration](docs/configuration.md).

## MCP Client Setup

### Claude Code

Add MCP server config to project `.mcp.json`:

```json
{
  "mcpServers": {
    "ogm": {
      "command": "uvx",
      "args": ["ogm-agent-bridge"],
      "env": {
        "OGM_BASE_URL": "${OGM_BASE_URL}",
        "OGM_API_KEY": "${OGM_API_KEY}",
        "OGM_PROJECT_ID": "${OGM_PROJECT_ID}",
        "OGM_PERMISSION_PROFILE": "${OGM_PERMISSION_PROFILE}"
      }
    }
  }
}
```

Verify:

```bash
claude mcp list
```

### OpenCode

Add MCP server config to `opencode.json` or `opencode.jsonc`:

```json
{
  "mcp": {
    "ogm": {
      "type": "local",
      "command": ["uvx", "ogm-agent-bridge"],
      "environment": {
        "OGM_BASE_URL": "{env:OGM_BASE_URL}",
        "OGM_API_KEY": "{env:OGM_API_KEY}",
        "OGM_PROJECT_ID": "{env:OGM_PROJECT_ID}",
        "OGM_PERMISSION_PROFILE": "{env:OGM_PERMISSION_PROFILE}"
      },
      "enabled": true
    }
  }
}
```

Restart OpenCode after editing config.

### Hermes

Add server under `mcp_servers`:

```yaml
mcp_servers:
  ogm:
    command: "uvx"
    args:
      - "ogm-agent-bridge"
    env:
      OGM_BASE_URL: "${OGM_BASE_URL}"
      OGM_API_KEY: "${OGM_API_KEY}"
      OGM_PROJECT_ID: "${OGM_PROJECT_ID}"
      OGM_PERMISSION_PROFILE: "${OGM_PERMISSION_PROFILE}"
    enabled: true
```

Verify:

```bash
hermes mcp test ogm
```

For source development, replace `uvx ogm-agent-bridge` with:

```bash
uv run --project /absolute/path/ogm-agent-bridge ogm-agent-bridge
```

MCP uses stdio. Diagnostics go to stderr.

## Use

After MCP server is connected, ask your agent to use OGM tools. Start with health and dataset discovery:

```text
Call ogm_health, then ogm_list_datasets.
```

Search entities in one dataset:

```json
{"dataset_id":"dataset-id","q":"OpenGraphMemory","limit":10}
```

Inspect graph context with `ogm_get_entity`, `ogm_get_neighbors`, `ogm_get_subgraph`, `ogm_get_graph`, or `ogm_find_path`. Use `ogm_get_relation_evidence` or `ogm_get_evidence` before making evidence-backed claims.

Retrieve relevant operational experience with `ogm_memory_search`. Create an episode, append attempts, and record a verified outcome only when profile is `personal-safe`. Feedback and supersession require `memory-curator`.

Upload documents only when profile is `personal-safe` and file path is under `OGM_UPLOAD_ROOTS`:

```text
Call ogm_upload_document with an approved local file path and dataset/project context.
```

## More Docs

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

Use project-scoped keys. Keep `.env` and keys outside upload roots. Start `read-only`; use `personal-safe` only for reviewed writes; reserve `memory-curator` for memory governance. See [security](docs/security.md).

## License

MIT. See [LICENSE](LICENSE).
