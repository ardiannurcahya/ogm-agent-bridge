# MCP Tools

Twenty-one tools. Project calls use configured project and return `{ok,data,provenance,warnings}`. Bridge preserves core response data and never invents citations.

## `ogm_health`

`GET /health`, no arguments, no project headers.

## `ogm_list_datasets`

`GET /v1/datasets`, no arguments.

## `ogm_search_entities`

`GET /v1/datasets/{dataset_id}/entities/search`.

| Argument | Rule |
|---|---|
| `dataset_id` | Required non-empty string. |
| `q` | Required 1..200 chars. |
| `entity_type` | Optional 1..100 chars. |
| `limit` | Optional integer 1..100. |

## `ogm_get_entity`

`GET /v1/entities/{entity_id}`. `entity_id` required.

## `ogm_get_neighbors`

`GET /v1/entities/{entity_id}/neighbors`. `entity_id` required; optional `limit` is 1..100.

## `ogm_find_path`

`GET /v1/datasets/{dataset_id}/graph/path`.

| Argument | Rule |
|---|---|
| `dataset_id`, `source_entity_id`, `target_entity_id` | Required non-empty strings. |
| `max_depth` | Optional integer 1..4. |
| `relation_limit` | Optional integer 1..200. |

## `ogm_get_subgraph`

`GET /v1/datasets/{dataset_id}/graph/subgraph`.

| Argument | Rule |
|---|---|
| `dataset_id`, `entity_id` | Required non-empty strings. |
| `depth` | Optional integer 0..2. |
| `node_limit` | Optional integer 1..200. |
| `relation_limit` | Optional integer 1..400. |

## `ogm_get_graph`

`GET /v1/datasets/{dataset_id}/graph`. `dataset_id` required; optional `limit` is 1..200 and `depth` is 0..1.

## `ogm_get_evidence`

`GET /v1/evidence/{evidence_id}`. `evidence_id` required.

## `ogm_get_relation_evidence`

`GET /v1/datasets/{dataset_id}/relations/{relation_id}/evidence`. `dataset_id` and `relation_id` required; optional `limit` is 1..100.

## `ogm_upload_document`

Multipart `POST /v1/datasets/{dataset_id}/documents`. Only `personal-safe` permits upload.

| Argument | Rule |
|---|---|
| `dataset_id` | Required UUID. |
| `path` | Required regular local file under `OGM_UPLOAD_ROOTS`. |
| `filename`, `mime_type` | Optional non-empty strings. |

Upload crosses local trust boundary. Review path and content first. See [security](security.md).

## `ogm_memory_list_episodes`

`GET /v1/agent-memory/episodes`. Available to all profiles.

| Argument | Rule |
|---|---|
| `status` | Optional `open`, `active`, `degraded`, `superseded`, or `rejected`. |
| `limit` | Optional integer 1..100. |

## `ogm_memory_get_episode`

`GET /v1/agent-memory/episodes/{episode_id}`. Available to all profiles. `episode_id` must be a `mem_` UUID identifier.

## `ogm_memory_search`

`GET /v1/agent-memory/search`. Available to all profiles. Search records an upstream retrieval audit. Results are historical claims, not independent proof; inspect the returned verifiers and evidence.

| Argument | Rule |
|---|---|
| `q` | Required non-blank string 1..512 chars. |
| `problem_signature` | Optional non-blank string 1..512 chars. |
| `repository`, `environment` | Optional non-blank strings 1..255 chars. |
| `include_inactive` | Optional boolean. |
| `limit` | Optional integer 1..100. |

## `ogm_memory_create_episode`

`POST /v1/agent-memory/episodes`. Requires `personal-safe` or `memory-curator`.

| Argument | Rule |
|---|---|
| `domain` | Required: `engineering`, `trading`, `research`, `operations`, or `custom`. |
| `title` | Required non-blank string 1..255 chars. |
| `goal` | Required non-blank string 1..10,000 chars. |
| `problem_signature` | Required non-blank string 1..512 chars. |
| `scope`, `metadata` | Optional bounded JSON objects. |
| `tags` | Optional 0..32 non-blank strings, each up to 64 chars. |
| `evidence` | Optional 0..32 reference/metadata objects. |

## `ogm_memory_append_attempt`

`POST /v1/agent-memory/episodes/{episode_id}/attempts`. Requires `personal-safe` or `memory-curator`. `hypothesis` is required; `result` is `success`, `failed`, or `partial`. Actions, notes, and metadata are bounded.

## `ogm_memory_record_outcome`

`POST /v1/agent-memory/episodes/{episode_id}/outcomes`. Requires `personal-safe` or `memory-curator`. `status` and `summary` are required. Verifiers are structured metadata only: the bridge never executes a submitted command.

## Curator Tools

The following require `memory-curator`; use them only after explicit review. Core feedback and supersession change the way future retrieval ranks or treats prior memory.

## `ogm_memory_feedback_episode`

`POST /v1/agent-memory/episodes/{episode_id}/feedback`, score `-1`, `0`, or `1`.

## `ogm_memory_supersede_episode`

`POST /v1/agent-memory/episodes/{episode_id}/supersede`, requires a distinct `superseding_episode_id`.

## `ogm_memory_feedback_pattern`

`POST /v1/agent-memory/patterns/{pattern_key}/feedback`, score `-1`, `0`, or `1`.

## `ogm_memory_supersede_pattern`

`POST /v1/agent-memory/patterns/{pattern_key}/supersede`, requires a distinct normalized pattern key.
