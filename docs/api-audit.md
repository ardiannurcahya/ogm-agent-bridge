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
- `POST /v1/agent-memory/episodes`
- `GET /v1/agent-memory/episodes`
- `GET /v1/agent-memory/episodes/{episode_id}`
- `POST /v1/agent-memory/episodes/{episode_id}/attempts`
- `POST /v1/agent-memory/episodes/{episode_id}/outcomes`
- `GET /v1/agent-memory/search`
- `POST /v1/agent-memory/episodes/{episode_id}/feedback`
- `POST /v1/agent-memory/episodes/{episode_id}/supersede`
- `POST /v1/agent-memory/patterns/{pattern_key}/feedback`
- `POST /v1/agent-memory/patterns/{pattern_key}/supersede`

Project requests require `X-API-Key` and `X-Project-Id`. Core scopes out-of-project resources as `404`. Agent Memory writes disable HTTP retries because an upstream gateway failure can leave an ambiguous accepted write. Bridge exposes no unsupported session, destructive mutation, or admin route.
