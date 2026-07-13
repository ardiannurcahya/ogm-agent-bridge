# MCP tools 0.1.0

All successful tools return envelope below. All project calls use configured project scope.

## Tool response envelope

```json
{
  "ok": true,
  "data": {},
  "provenance": {
    "project_id": "...",
    "dataset_id": "...",
    "session_id": "...",
    "trace_id": "..."
  },
  "warnings": []
}
```

Omit optional provenance keys when unavailable. Failure is structured MCP tool error, not success envelope.

## `ogm_health`

- Risk: read. Permission: `health` allow.
- Description: Core liveness check.
- Input: none.
- Core: `GET /health`.
- Output `data`: `{status: "ok"}`.
- Errors: upstream timeout/transport; unexpected core failure.
- Note: no project auth required by core.

## `ogm_list_datasets`

- Risk: read. Permission: `datasets:read` allow.
- Description: List datasets visible in configured project.
- Input: none.
- Core: `GET /v1/datasets`.
- Output `data`: `[{id, project_id, name, description?, metadata, status, error_message?}]`.
- Errors: `401`, timeout, `502`, `503`.

## `ogm_query`

- Risk: read. Permission: `query:read` allow.
- Description: Grounded retrieval. Preserve answer, citations, retrieval trace, usage.
- Input: `dataset_id` string required; `query` string required, 1..10,000; `mode` optional `vector_only|graph_only|hybrid`, default `vector_only`; `top_k` optional int 1..50, default 5; `graph_depth` optional int 1..2; `graph_fanout` optional int 1..100; `graph_timeout_ms` optional int 1..10,000; `fusion` optional `rrf|weighted`; `session_id` optional bridge/core session ID; `memory_top_k` optional int 0..20, default 0.
- Core: `POST /v1/query`; map resolved session to `memory_session_id`; mapping supplies `memory_user_id` and `memory_agent_id` when session used.
- Output `data`: `{answer, citations: [{index, chunk_id, document_id, score, text}], retrieval_trace, usage}`. Provenance includes dataset/session/trace IDs.
- Errors: validation `422`; `401`; dataset/session `404`; timeout; `502`; `503`.
- Note: memory retrieval fields need session context. Core citation text stays unchanged.

## `ogm_search_memory`

- Risk: read. Permission: `memory:read` allow.
- Description: Search stored facts.
- Input: `query` string required, 1..5000; `session_id` optional; `scopes` optional array of `user|agent|session`, defaults all; `limit` optional int 1..50, default 10; `include_superseded` optional bool, default false.
- Core: `POST /v1/memory/search`; resolved session supplies `user_id`, `agent_id`, `session_id`.
- Output `data`: facts with `{id, scope, subject, predicate, value, content, confidence, status, provenance, metadata, valid_from, ... score, matched_terms}`.
- Errors: validation `422`; `401`; referenced scope/session `404`; timeout; `502`; `503`.
- Note: lexical search only. Do not present as semantic retrieval.

## `ogm_create_session`

- Risk: write. Permission: `memory:write` allow in personal-safe.
- Description: Provision core user+agent if absent; create session; persist SQLite mapping.
- Input: `user_external_id` string required, 1..255; `agent_name` string required, 1..255; `user_display_name` optional string <=255; `agent_description` optional string <=5000; `title` optional string <=255; `metadata` optional object.
- Core: conditional `POST /v1/memory/users`, conditional `POST /v1/memory/agents`, then `POST /v1/memory/sessions`.
- Output `data`: `{session_id, core_session_id, user_id, agent_id, title, metadata, archived_at}`. Provenance includes project/session IDs.
- Errors: permission denied; validation `422`; `401`; identity/session `404`; timeout; `502`; `503`.
- Note: core session requires existing user and agent. SQLite retains mapping because core has no session list endpoint.

## `ogm_remember`

- Risk: write. Permission: `memory:write` allow in personal-safe.
- Description: Store one fact through mandatory message batch.
- Input: `session_id` string required; `message` object required: `role` one of `system|user|assistant|tool`, `content` 1..50,000, optional `metadata`; `fact` object required: `scope` optional `user|agent|session`, default `user`; `subject` 1..255; `predicate` 1..100; `value` 1..5000; `confidence` optional int 0..100 default 100; `metadata` optional object.
- Core: `POST /v1/memory/sessions/{core_session_id}/messages` with one message and one fact.
- Output `data`: `{messages: [...], facts: [...]}`; fact follows core FactView shape. Provenance includes session ID.
- Errors: permission denied; validation `422`; `401`; unknown session `404`; timeout; `502`; `503`.
- Note: requires `session_id` from `ogm_create_session`. Facts cannot be posted alone.

## `ogm_upload_document`

- Risk: write. Permission: `documents:write` allow in personal-safe.
- Description: Upload one document into existing dataset.
- Input: `dataset_id` string required; `filename` string required; `content` string/base64 bytes required; `mime_type` string required. Handler converts to multipart field `file`; enforce core upload/type/size limits without claiming bridge-specific limit.
- Core: `POST /v1/datasets/{dataset_id}/documents` multipart.
- Output `data`: `{id, project_id, dataset_id, filename, mime_type, size_bytes, content_hash, object_key, status, error_message?, duplicate, created_at, updated_at}`.
- Errors: permission denied; `401`; dataset `404`; `413`; `415`; timeout; `502`; `503`.
- Note: same content hash in same project/dataset yields existing document with `duplicate: true`.
