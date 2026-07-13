# Architecture

## Overview

Thin bridge over OpenGraphMemory REST. One stdio MCP server serves Claude Code, OpenCode, Hermes. One bridge process maps to one project; config supplies project API key and project ID.

```text
Claude Code ─┐
OpenCode ────┼─ MCP stdio ─ tool handler ─ HTTP client ─ OpenGraphMemory REST
Hermes ──────┘                 │                 │
                               └─ SQLite state ───┘
```

## Components

- **Config.** Load `.env` and environment: base URL, API key, project ID, timeout, retries, permission profile, SQLite path.
- **HTTP client.** Async REST client. Send `X-API-Key` and `X-Project-Id` on project calls. Bounded retries for transient transport/`502`/`503`; configured timeout. Preserve core response fields needed by tools.
- **MCP server.** Stdio transport only in 0.1.0. Stdout reserved for MCP protocol.
- **Tool handlers.** Validate MCP input, permission-check, call client, return common envelope and provenance.
- **Permission layer.** Hardcoded 0.1.0 allowlist. `read-only`: reads only. `personal-safe`: reads plus create session, remember, upload document. No `full` profile. No destructive calls.
- **State store.** Local SQLite. Stores harness-facing session mapping plus provisioned core user/agent IDs. Never stores project API key.

## Session model

`ogm_create_session` takes stable harness identity inputs (`user_external_id`, `agent_name`) and optional title/metadata. Handler checks SQLite provisioned identity table. Missing user: call `POST /v1/memory/users`; missing agent: call `POST /v1/memory/agents`; save returned core IDs. Call `POST /v1/memory/sessions`, then save bridge session mapping: bridge session ID, core session ID, project ID, user ID, agent ID, harness identity, timestamps.

Core currently has no user/agent lookup or upsert route. SQLite loss can therefore leave existing core identities unrecoverable through public API. Backup/restore is documented compatibility limitation. Never silently create duplicate agents after state loss.

No core list-session/list-message API. SQLite mapping is source for bridge recovery and `ogm_remember` routing. `ogm_remember` resolves bridge `session_id` to core `session_id`, then posts one message plus requested fact in messages batch. `ogm_query` does not resolve bridge IDs: B1 query currently accepts core IDs directly; B2 mapping is only resolved by remember.

## Auth and secrets

Every project call sends two headers: `X-API-Key`, `X-Project-Id`. Keys, authorization headers, raw secret values, and sensitive configured fields must be redacted from logs/errors. Never write logs to stdout; stdio MCP would corrupt. Log structured diagnostics to stderr only.

## Error handling

Convert core/transport failures to structured MCP tool errors. Include stable bridge code, safe message, HTTP status when present, retryability, provenance trace ID when available. Do not leak secret/header/body data.

| Core condition | Bridge code | Meaning |
|---|---|---|
| `401` | `AUTH_FAILED` | Invalid/missing project credentials |
| `404` | `NOT_FOUND` | Unknown or out-of-project resource/session |
| `413` | `PAYLOAD_TOO_LARGE` | Upload/body exceeds core limit |
| `415` | `UNSUPPORTED_MEDIA_TYPE` | File type rejected |
| `502` | `UPSTREAM_BAD_GATEWAY` | Retryable core/upstream failure |
| `503` | `UPSTREAM_UNAVAILABLE` | Retryable unavailable dependency/service |
| timeout/transport | `UPSTREAM_TIMEOUT` / `UPSTREAM_TRANSPORT` | Bounded retry then fail |
| `422` | `VALIDATION_FAILED` | Input violates core constraint |

## State repair

SQLite schema v3 blocks a session after ambiguous `remember` timeout, transport, `502`, or `503`. Later writes fail closed. No automatic repair: inspect core first, then manually repair or replace local state only after confirmed outcome.

## Out of scope: 0.1.0

No cross-harness session sync; automatic conversation ingestion; manifest generator; full permission-policy engine; OpenClaw plugin; destructive tools; HTTP MCP transport. No direct PostgreSQL, Qdrant, Neo4j, object-store access. No admin/project creation.
