# ogm-agent-bridge

MCP stdio bridge for [OpenGraphMemory](https://github.com/ardiannurcahya/open-graph-memory). One bridge process connects one core project to Claude Code, OpenCode, or Hermes.

```text
Claude Code ─┐
OpenCode ────┼─ MCP stdio ─ ogm-agent-bridge ─ OpenGraphMemory REST
Hermes ──────┘
```

Bridge calls core REST only. No direct database, vector, graph, or object-store access. Seven tools cover health, datasets, retrieval, memory search, session creation, remembering facts, and local-file upload. No destructive tools exist.

## Start from source

Source install is current reliable setup. Package version is `0.1.0`, but no `v0.1.0` tag or PyPI publication exists yet.

```bash
git clone https://github.com/ardiannurcahya/ogm-agent-bridge.git "$HOME/src/ogm-agent-bridge"
cd "$HOME/src/ogm-agent-bridge"
uv sync --locked
cp .env.example .env
# Edit .env. Set OGM_API_KEY and OGM_PROJECT_ID.
uv run ogm-agent-bridge
```

Server uses stdio. Keep stdout for MCP protocol. Logs go to stderr.

`uvx ogm-agent-bridge` becomes valid **after 0.1.0 is published to PyPI**. Until then use source command above.

## Configure harness

- [Claude Code](docs/claude-code.md)
- [OpenCode](docs/opencode.md)
- [Hermes](docs/hermes.md)

Harness examples use source command and environment variables. See [configuration](docs/configuration.md) for exact variables, permission profiles, upload roots, and separate named project configs.

## First workflow

1. Configure core connection in `.env`.
2. Register bridge in harness guide above.
3. Call `ogm_health`, then `ogm_list_datasets`.
4. Call `ogm_query` with dataset ID.
5. For memory writes, call `ogm_create_session`; retain returned bridge `session_id`; call `ogm_remember`.
6. Upload only approved local files with `ogm_upload_document`.

Copyable arguments, schemas, envelopes, and errors: [tools](docs/tools.md). Session IDs have important limits: [session lifecycle](docs/session-lifecycle.md).

## Operations

- [Security](docs/security.md): credentials, uploads, permissions, exfiltration boundary.
- [Backup and recovery](docs/backup-recovery.md): SQLite backup, ambiguity repair, state-loss limit.
- [Troubleshooting](docs/troubleshooting.md)
- [Resource guidance](docs/resource-guidance.md)
- [Upgrade and uninstall](docs/upgrade-uninstall.md)

Engineering records: [architecture](docs/architecture.md), [core API audit](docs/api-audit.md), [conformance](docs/conformance.md), [release](docs/release.md), [plan](docs/plan.md).

## Validate source checkout

```bash
uv sync --dev --locked
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest -q
```

## License

MIT. See [LICENSE](LICENSE).
