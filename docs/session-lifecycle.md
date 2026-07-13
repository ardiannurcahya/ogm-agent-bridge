# Session lifecycle

## IDs

`ogm_create_session` returns two IDs:

- `session_id`: bridge-generated ID. Stored in local SQLite. Use only with `ogm_remember`.
- `core_session_id`: OpenGraphMemory session ID. Core API uses this ID.

It also returns core `user_id` and `agent_id`.

## Create

`ogm_create_session` accepts `user_external_id` and stable `agent_name`. Bridge checks local state for mapped identities. Missing mappings trigger core user/agent creation, then core session creation. Successful mapping persists in `OGM_STATE_DB`.

Inputs map exactly:

- User: `user_display_name`, `user_metadata`
- Agent: `agent_description`, `agent_metadata`
- Session: `title`, `session_metadata`

A normal restart keeps active mappings when same state database remains.

## Remember

`ogm_remember` takes bridge `session_id`. Bridge resolves it to core session ID and posts one message plus one fact. Unknown, uncertain, or blocked mappings fail closed.

Do not call `ogm_remember` again after timeout, transport failure, or ambiguous write error. Bridge blocks session writes because core may already have accepted batch. Follow [backup and recovery](backup-recovery.md).

## Query limitation

B1 `ogm_query` does not look up bridge session mapping. Its `memory_user_id`, `memory_agent_id`, and `memory_session_id` fields pass directly to core. Supply core IDs only. `core_session_id` from create response is valid for `memory_session_id`; bridge `session_id` is not.

B2 mapping resolution exists only in `ogm_remember`. This is current limitation, not cross-tool session support.

`ogm_search_memory` also forwards `user_id`, `agent_id`, and `session_id` directly to core. Use core IDs.

## Failure and state loss

Core has no public user/agent lookup or session list endpoint usable by bridge. If SQLite state is lost, bridge cannot safely recover existing core identity/session mappings. It must not blindly recreate them: duplicate or uncertain identities may result.

Restore state backup first. If unavailable, inspect core through approved operator path, record verified IDs, and repair or replace local state only under controlled procedure. See [backup and recovery](backup-recovery.md). No automatic repair exists.

Related: [tools](tools.md), [configuration](configuration.md), [architecture](architecture.md), [API audit](api-audit.md).
