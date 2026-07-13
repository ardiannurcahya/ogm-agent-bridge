# ogm-agent-bridge

Agent harness bridge for [OpenGraphMemory](https://github.com/ardiannurcahya/open-graph-memory).

Exposes OpenGraphMemory knowledge retrieval and agent memory to AI coding
harnesses through a single MCP server, with adapters for **Claude Code**,
**OpenCode**, and **Hermes**.

## Status

B3 implemented: versioned Claude Code, OpenCode, and Hermes MCP examples plus
setup, trust, verification, and troubleshooting docs. B2 read and write tools
remain available; SQLite durable state maps local session IDs to core IDs.

Harness setup: [Claude Code](docs/claude-code.md), [OpenCode](docs/opencode.md),
and [Hermes](docs/hermes.md).

## Development run

```bash
uv sync
uv run ogm-agent-bridge
```

Server uses stdio. Keep stdout reserved for MCP protocol. Configure
`OGM_BASE_URL`, `OGM_API_KEY`, and `OGM_PROJECT_ID`; `ogm_health` calls core
`/health` without project headers.

## What it does

The bridge is a thin layer over the OpenGraphMemory REST API. It does not talk
to PostgreSQL, Qdrant, or Neo4j directly — every operation goes through the
core API using its `X-API-Key` + `X-Project-Id` auth model.

```text
Claude Code ─┐
OpenCode ────┼── ogm-agent-bridge (MCP) ── OpenGraphMemory API
Hermes ──────┘
```

## Tools (target for 0.1.0)

| Tool | Risk | Purpose |
|---|---|---|
| `ogm_health` | read | Check API and dependency readiness |
| `ogm_list_datasets` | read | List datasets in the project |
| `ogm_query` | read | Grounded retrieval (vector / graph / hybrid) with citations |
| `ogm_search_memory` | read | Lexical search over stored memory facts |
| `ogm_create_session` | write | Create a memory session (auto-provisions user + agent) |
| `ogm_remember` | write | Store a memory fact within a session |
| `ogm_upload_document` | write | Upload a document to a dataset |

## Configuration

Copy `.env.example` to `.env` and fill in your OpenGraphMemory connection:

```bash
cp .env.example .env
```

```env
OGM_BASE_URL=http://localhost:8000
OGM_API_KEY=<project-api-key>
OGM_PROJECT_ID=<project-uuid>
OGM_STATE_DB=~/.local/state/ogm-agent-bridge/state.db
OGM_PERMISSION_PROFILE=personal-safe
```

One bridge instance maps to one OpenGraphMemory project (the API auth model is
per-project). State database gets mode `0600`. `read-only` denies B2 writes;
`personal-safe` allows them. Agent name is identity key: keep it stable.

## Recovery limitation

Normal restart reuses active SQLite mappings. Core has no public identity/session
lookup. Lost state, timeout, or transport failure during provisioning becomes
`uncertain`; bridge fails closed and never blindly retries POST. Inspect core
before manual recovery.

## License

MIT — see [LICENSE](LICENSE).
