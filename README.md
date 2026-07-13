# ogm-agent-bridge

Agent harness bridge for [OpenGraphMemory](https://github.com/ardiannurcahya/open-graph-memory).

Exposes OpenGraphMemory knowledge retrieval and agent memory to AI coding
harnesses through a single MCP server, with adapters for **Claude Code**,
**OpenCode**, and **Hermes**.

## Status

Early development. See [`docs/plan.md`](docs/plan.md) for the full roadmap and
milestone breakdown.

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
```

One bridge instance maps to one OpenGraphMemory project (the API auth model is
per-project).

## License

MIT — see [LICENSE](LICENSE).
