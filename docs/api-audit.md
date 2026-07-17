# Core API Audit

Bridge targets current OpenGraphMemory structured graph REST contract.

- `GET /health`
- `GET /v1/datasets`
- `POST /v1/datasets/{dataset_id}/documents`
- `GET /v1/datasets/{dataset_id}/entities/search`
- `GET /v1/entities/{entity_id}`
- `GET /v1/entities/{entity_id}/neighbors`
- `GET /v1/datasets/{dataset_id}/graph/path`
- `GET /v1/datasets/{dataset_id}/graph/subgraph`
- `GET /v1/datasets/{dataset_id}/graph`
- `GET /v1/evidence/{evidence_id}`
- `GET /v1/datasets/{dataset_id}/relations/{relation_id}/evidence`

Project requests require `X-API-Key` and `X-Project-Id`. Core scopes out-of-project resources as `404`. Bridge exposes no unsupported query, memory, session, mutation, or admin route.
