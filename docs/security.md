# Security

## Credentials

Set `OGM_API_KEY` and `OGM_PROJECT_ID` in harness environment or protected `.env`. Do not commit `.env`, keys, copied MCP configs containing keys, SQLite backups, or logs. Project calls send both `X-API-Key` and `X-Project-Id`. Bridge logs to stderr; stdout is MCP protocol.

Use separate API keys, state DBs, and upload roots per project. Core authorization remains final boundary; bridge permission profile is local guard.

## Permissions

Use `read-only` unless writes needed. `personal-safe` permits only create session, remember, and upload. No `full` profile. No delete, update, project-admin, or direct-storage tools are registered. Absence of destructive tools limits bridge actions; it does not make uploaded data safe.

## Upload boundary

`ogm_upload_document` reads bytes from local `path` then transmits them to configured OpenGraphMemory endpoint. This is data exfiltration boundary. Agent-selected path can expose secrets if root is broad.

Use these controls:

1. Set `OGM_UPLOAD_ROOTS` to dedicated reviewed directory, not `$HOME`, `/`, repository root with secrets, or temp shared directory.
2. Review path, resolved symlink target, filename, and content before upload.
3. Keep credentials, `.env`, SSH material, browser profiles, build secrets, and SQLite state outside upload roots.
4. Use `read-only` for harnesses that do not need upload.
5. Treat remote core retention, access controls, backups, and logs as separate security domain.

Bridge resolves symlinks and requires regular file inside root. This prevents path escape, not disclosure of approved-root files.

## State

`OGM_STATE_DB` stores bridge/core ID mappings and identity state, not API key. Protect it as sensitive metadata: mode 0600 where filesystem supports it, owner-only directory, encrypted backup when needed. State loss causes unrecoverable mapping ambiguity; see [backup and recovery](backup-recovery.md).

## Network and core

Use TLS endpoint for remote core. Verify base URL points to intended project service. Do not expose stdio bridge as network service. Core API has broader routes than bridge; protect core separately.

Related: [configuration](configuration.md), [tools](tools.md), [architecture](architecture.md), [API audit](api-audit.md).
