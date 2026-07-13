# Troubleshooting

## Startup config error

Check required values and rules:

```bash
printf '%s\n' "$OGM_BASE_URL" "$OGM_PROJECT_ID"
uv run ogm-agent-bridge --version
```

`OGM_PROJECT_ID` must be UUID. `OGM_TIMEOUT_SECONDS` must be positive. `OGM_MAX_RETRIES` must be non-negative integer. Profile only `read-only` or `personal-safe`. See [configuration](configuration.md).

## MCP does not connect

Use harness docs and source command exactly: [Claude Code](claude-code.md), [OpenCode](opencode.md), [Hermes](hermes.md). Do not print diagnostics to stdout. Check harness process environment has all three required OGM variables.

## Health works; project tools return authentication error

`ogm_health` is unauthenticated. `ogm_list_datasets` proves project credentials. Check API key and project UUID pair. Core returns `404` for out-of-project resource; do not infer resource exists elsewhere.

## Write denied

Set `OGM_PERMISSION_PROFILE=personal-safe`, restart bridge, then retry only clean operation. `read-only` denies session, remember, upload. No `full` profile.

## Upload rejects path

Use `path`, not content. It must resolve to regular file under `OGM_UPLOAD_ROOTS`. Check current directory because default root is resolved process cwd. Symlink target must remain in root. Core may still reject size with `payload_too_large` or type with `unsupported_media`.

## Query or search finds no memory

Use core IDs in query fields: `memory_user_id`, `memory_agent_id`, `memory_session_id`. Do not use bridge `session_id`. Search `user_id`, `agent_id`, `session_id` also need core IDs. Search is lexical. See [session lifecycle](session-lifecycle.md) and [tools](tools.md).

## Create or remember says uncertain

Do not retry write. Provisioning or message may have reached core. Preserve state, inspect outcome, then recover under [backup and recovery](backup-recovery.md). State loss cannot be automatically rebuilt.

## Timeout or upstream errors

Check core health, network route, TLS, and `OGM_TIMEOUT_SECONDS`. Reads may retry eligible transient failures; writes intentionally do not retry. Increase timeout only after checking core latency.

## Docs/test check

```bash
uv run pytest -q
```

Docs verification test checks required docs and links, environment defaults, seven tool names, and stale phrases.
