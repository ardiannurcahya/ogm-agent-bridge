# OpenGraphMemory core API audit

Factual REST contract verified against OpenGraphMemory core commit `7703d3994b49272bef7b0d38caf896cde4338f13`. Bridge calls core only. Default direct API base URL is `http://localhost:8000`; paths below are used as written, for example `http://localhost:8000/v1/query`. A reverse proxy may expose a different external base URL, configured through `OGM_BASE_URL`.

## Auth model

Project-scoped calls require both headers:

```text
X-API-Key: <project-api-key>
X-Project-Id: <project-id>
```

Key and project scope every resource. Cross-project resource access returns `404`, not resource details. `GET /health` and `GET /ready` are unauthed. Admin-only `POST /v1/projects` uses admin `X-API-Key` only; bridge 0.1.0 does not call it.

## Query

### `POST /v1/query`

JSON request:

| Field | Type | Required | Constraint/default |
|---|---|---|---|
| `dataset_id` | string | yes | Existing dataset in project |
| `query` | string | yes | 1..10,000 chars |
| `mode` | `vector_only` \| `graph_only` \| `graph_local` \| `graph_global` \| `hybrid` | no | `vector_only`; no `auto` |
| `top_k` | integer | no | 1..50; `5` |
| `graph_depth` | integer | no | 1..2 |
| `graph_fanout` | integer | no | 1..100 |
| `graph_timeout_ms` | integer | no | 1..10,000 |
| `fusion` | `rrf` \| `weighted` | no | Used by hybrid |
| `memory_user_id` | string | no | Existing scoped user |
| `memory_agent_id` | string | no | Existing scoped agent |
| `memory_session_id` | string | no | Existing scoped session |
| `memory_top_k` | integer | no | 0..20; `0` |
| `include_communities` | boolean | no | Include communities |
| `community_level` | integer | no | 0..2 |

Response: `{answer: string, citations: [{index, chunk_id, document_id, score, text}], retrieval_trace: {trace_id?, mode?, latency_ms?, chunk_ids: [], scores: [], ...}, usage: {prompt_tokens, completion_tokens, total_tokens, estimated_cost_usd}}`.

## Memory

### Identity and session

`POST /v1/memory/users`: `{external_id: string(1..255), display_name?: string(<=255), metadata?: object}` → `{id, project_id, external_id, display_name, metadata}`.

`POST /v1/memory/agents`: `{name: string(1..255), description?: string(<=5000), metadata?: object}` → `{id, project_id, name, description, metadata}`.

`POST /v1/memory/sessions`: `{user_id: string, agent_id: string, title?: string(<=255), metadata?: object}`. User and agent must already exist in project. → `{id, project_id, user_id, agent_id, title, metadata, archived_at}`.

### Messages, facts, context, search

`POST /v1/memory/sessions/{session_id}/messages`: `{messages: Message[1..50], facts?: Fact[0..50]}` → `{messages: [MessageView], facts: [FactView]}`. `Message`: `{role: system|user|assistant|tool, content: string(1..50,000), metadata?: object}`. `Fact`: `{scope?: user|agent|session (user), subject: string(1..255), predicate: string(1..100), value: string(1..5000), confidence?: integer(0..100, 100), metadata?: object}`.

`GET /v1/memory/sessions/{session_id}/memory` → `[FactView]`.

`GET /v1/memory/users/{user_id}/context?limit=20` → `[FactView]`.

`POST /v1/memory/search`: `{query: string(1..5000), user_id?, agent_id?, session_id?, scopes?: [user|agent|session] (all three), limit?: integer(1..50, 10), include_superseded?: boolean(false)}` → `[MemorySearchHit]`. Search is lexical, returns score and matched terms.

`DELETE /v1/memory/{memory_id}` → `204`.

`FactView`: `{id, project_id, user_id?, agent_id?, session_id?, scope, subject, predicate, value, content, confidence, status, supersedes_id?, source_message_id?, provenance, metadata, valid_from, valid_until?, deleted_at?}`. `MemorySearchHit` adds `{score, matched_terms: string[]}`. `MessageView` adds `{id, project_id, session_id, created_at}`.

## Datasets

`POST /v1/datasets`: `{name: string(1..255), description?: string(<=5000), metadata?: object}` → `201 Dataset`.

`GET /v1/datasets` → `Dataset[]`.

`GET /v1/datasets/{dataset_id}` → `Dataset`.

`PATCH /v1/datasets/{dataset_id}`: any of `{name: string(1..255), description: string|null(<=5000), metadata: object|null}` → `Dataset`.

`DELETE /v1/datasets/{dataset_id}` → `204`.

`Dataset`: `{id, project_id, name, description?, metadata, status, error_message?}`. Dataset name unique per project.

## Documents

`POST /v1/datasets/{dataset_id}/documents`: multipart form field `file` required. Core validates file type/content and streams upload. → `201 Document`.

`GET /v1/datasets/{dataset_id}/documents` → `Document[]`.

`GET /v1/datasets/{dataset_id}/documents/{document_id}` → `Document`.

`GET /v1/documents/{document_id}` → `Document`.

`DELETE /v1/documents/{document_id}` → `204`.

`Document`: `{id, project_id, dataset_id, filename, mime_type, size_bytes, content_hash, object_key, status, error_message?, duplicate: boolean, created_at, updated_at}`. Same content hash in same project/dataset returns existing document with `duplicate: true`.

## Graph

`GET /v1/entities/{entity_id}` → `Entity`.

`GET /v1/entities/{entity_id}/neighbors?limit=25` → `[{relation: Relation, entity: Entity}]`; limit constraint 1..100.

`GET /v1/datasets/{dataset_id}/graph?limit=100&depth=1` → `GraphSummary`; `limit` 1..200, `depth` 0..1. This differs from `POST /v1/query`, whose `graph_depth` accepts 1..2.

`GET /v1/datasets/{dataset_id}/graph/explorer?node_limit=1..200&relation_limit=1..200&community_level=0..2` → graph explorer response.

`GET /v1/datasets/{dataset_id}/community-reports?community_level=0..2` → community report list.

`GET /v1/datasets/{dataset_id}/community-reports/{report_id}` → community report.

`GET /v1/datasets/{dataset_id}/community-report-jobs` → community report job list.

`GET /v1/evidence/{evidence_id}` → `Evidence`.

`GET /v1/graph-runs/{run_id}` → `GraphRun`.

`GET /v1/graph-jobs/{job_id}` → `GraphJob`.

`PATCH /v1/relations/{relation_id}/review`: `{review_state: string}` → `Relation`.

`Entity`: `{id, dataset_id, canonical_name, entity_type, confidence, version, review_state}`. `Relation`: `{id, dataset_id, source_entity_id, target_entity_id, relation_type, confidence, extractor_version, review_state, citations: [{dataset_id, document_id, chunk_id, quote}]}`. `GraphSummary`: `{dataset_id, entity_count, relation_count, nodes: Entity[], relations: Relation[]}`. Evidence/run/job expose identifiers, dataset/document/chunk, status and extraction metadata; evidence includes quote/citation fields and offsets.

## Health

`GET /health` → `{"status":"ok"}`.

`GET /ready` → dependency readiness object; status reflects readiness.

`GET /metrics` returns Prometheus text; excluded from schema.

## Gaps and implications for bridge

- No list sessions/messages endpoint. Bridge stores mapping and provisioned identity state itself.
- No get/list/upsert endpoint for memory users or agents. Core user creation is unique by `(project_id, external_id)`, while agent names are not a stable lookup contract. If local SQLite state is lost, bridge cannot reliably recover existing core identity IDs. B2 therefore needs either core lookup/upsert endpoints or an explicit state backup/recovery limitation.
- Fact only enters through session messages batch. `remember` needs session.
- Search is lexical only. Do not over-rely on it for semantic recall.
- Session needs existing user plus agent. `create_session` auto-provisions both.
