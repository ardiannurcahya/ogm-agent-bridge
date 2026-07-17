# MCP Tools

Eleven tools. Project calls use configured project and return `{ok,data,provenance,warnings}`. Bridge preserves core response data and never invents citations.

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
