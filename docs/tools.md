# MCP tools

Seven tools. All project calls use configured project. Input examples are copyable JSON argument objects.

## Envelopes

Success:

```json
{"ok":true,"data":{},"provenance":{"project_id":"..."},"warnings":[]}
```

`provenance` keys appear only when known: `project_id`, `dataset_id`, `session_id`, `trace_id`.

Failure returns tool result, not success envelope:

```json
{"ok":false,"error":{"code":"validation_error","message":"dataset_id must be a UUID"}}
```

Codes: `authentication_error`, `permission_denied`, `not_found`, `validation_error`, `payload_too_large`, `unsupported_media`, `upstream_error`, `timeout`, `transport_error`. Unexpected internal failures return `upstream_error` and `Internal bridge error`; no secret details.

## `ogm_health`

Schema: no arguments. Permission: read. Core: `GET /health` without project headers. Response `data` is core health object.

```json
{}
```

## `ogm_list_datasets`

Schema: no arguments. Permission: `datasets:read`. Core: `GET /v1/datasets`. Response `data` is core dataset array.

```json
{}
```

## `ogm_query`

Permission: `query:read`. Core: `POST /v1/query`. Response `data` preserves core `{answer, citations, retrieval_trace, usage}`.

| Argument | Type | Required | Rule/default |
|---|---|---:|---|
| `dataset_id` | string | yes | Non-empty. Core dataset ID. |
| `query` | string | yes | 1..10,000 chars. |
| `mode` | string | no | `vector_only`, `graph_only`, `hybrid`; omitted lets core default `vector_only`. |
| `top_k` | integer | no | 1..50; core default `5`. |
| `graph_depth` | integer | no | 1..2. |
| `graph_fanout` | integer | no | 1..100. |
| `graph_timeout_ms` | integer | no | 1..10,000. |
| `fusion` | string | no | `rrf` or `weighted`. |
| `memory_user_id` | string | no | Core memory user ID. |
| `memory_agent_id` | string | no | Core memory agent ID. |
| `memory_session_id` | string | no | Core memory session ID. |
| `memory_top_k` | integer | no | 0..20; core default `0`. |

```json
{"dataset_id":"11111111-1111-1111-1111-111111111111","query":"What is retention policy?","mode":"hybrid","top_k":5,"memory_session_id":"core-session-id","memory_top_k":5}
```

**B1 ID rule:** query forwards `memory_user_id`, `memory_agent_id`, and `memory_session_id` unchanged. It accepts core IDs directly. It does **not** resolve bridge `session_id`. B2 mapping exists only in `ogm_remember`; do not pass returned bridge `session_id` as `memory_session_id` or imply bridge session works in query. See [session lifecycle](session-lifecycle.md).

## `ogm_search_memory`

Permission: `memory:read`. Core: `POST /v1/memory/search`. Response warning says search is lexical, not semantic.

| Argument | Type | Required | Rule/default |
|---|---|---:|---|
| `query` | string | yes | 1..5,000 chars. |
| `user_id` | string | no | Core user ID. |
| `agent_id` | string | no | Core agent ID. |
| `session_id` | string | no | Core session ID. Not bridge ID. |
| `scopes` | array | no | Elements `user`, `agent`, `session`; omitted lets core use all. |
| `limit` | integer | no | 1..50; core default `10`. |
| `include_superseded` | boolean | no | Core default `false`. |

```json
{"query":"retention","session_id":"core-session-id","scopes":["user","session"],"limit":10,"include_superseded":false}
```

## `ogm_create_session`

Permission: `memory:write`; only `personal-safe`. Creates/reuses locally mapped core user and agent, then creates core session. Exact metadata fields are separate.

| Argument | Type | Required | Rule |
|---|---|---:|---|
| `user_external_id` | string | yes | 1..255. |
| `agent_name` | string | yes | 1..255. Stable identity key. |
| `user_display_name` | string | no | 0..255. |
| `agent_description` | string | no | 0..5,000. |
| `title` | string | no | 0..255. |
| `user_metadata` | object | no | Sent only with user creation. |
| `agent_metadata` | object | no | Sent only with agent creation. |
| `session_metadata` | object | no | Sent only with session creation. |

```json
{"user_external_id":"me@example.com","agent_name":"claude-code","user_display_name":"Me","agent_description":"Coding assistant","title":"bridge docs","user_metadata":{"team":"docs"},"agent_metadata":{"harness":"claude"},"session_metadata":{"repo":"ogm-agent-bridge"}}
```

Response `data`: `{session_id, core_session_id, user_id, agent_id}`. `session_id` is bridge ID; retain for `ogm_remember`. Core session response fields such as `title`, `metadata`, and `archived_at` are not returned by bridge.

## `ogm_remember`

Permission: `memory:write`; only `personal-safe`. Resolves bridge `session_id` through local SQLite, then posts exactly one message and one fact to core batch endpoint.

| Argument | Type | Required | Rule |
|---|---|---:|---|
| `session_id` | string | yes | Active bridge session ID from `ogm_create_session`. |
| `message.role` | string | yes | `system`, `user`, `assistant`, `tool`. |
| `message.content` | string | yes | 1..50,000. |
| `message.metadata` | object | no | Sent with message. |
| `fact.scope` | string | no | `user`, `agent`, `session`; default `user`. |
| `fact.subject` | string | yes | 1..255. |
| `fact.predicate` | string | yes | 1..100. |
| `fact.value` | string | yes | 1..5,000. |
| `fact.confidence` | integer | no | 0..100; core default `100`. |
| `fact.metadata` | object | no | Sent with fact. |

```json
{"session_id":"bridge-session-id","message":{"role":"user","content":"Use uv for this project.","metadata":{"source":"chat"}},"fact":{"scope":"user","subject":"project","predicate":"uses","value":"uv","confidence":100,"metadata":{"verified":true}}}
```

Response `data`: core `{messages:[...],facts:[...]}`. Timeout, transport, or ambiguous upstream write blocks later writes for this bridge session; inspect before repair.

## `ogm_upload_document`

Permission: `documents:write`; only `personal-safe`. Core: multipart `POST /v1/datasets/{dataset_id}/documents` field `file`. File bytes come from local `path` inside approved upload roots.

| Argument | Type | Required | Rule |
|---|---|---:|---|
| `dataset_id` | string | yes | UUID. |
| `path` | string | yes | Non-empty local regular-file path inside `OGM_UPLOAD_ROOTS`. |
| `filename` | string | no | Non-empty multipart filename; defaults basename of `path`. |
| `mime_type` | string | no | Non-empty; defaults guessed type or `application/octet-stream`. |

```json
{"dataset_id":"11111111-1111-1111-1111-111111111111","path":"/home/me/project/docs/guide.md","filename":"guide.md","mime_type":"text/markdown"}
```

Response `data` preserves core document object. Core controls type and size limits. Upload sends selected file outside local machine: see [security](security.md).
