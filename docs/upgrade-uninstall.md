# Upgrade and uninstall

## Upgrade source checkout

Back up state first. Stop harnesses before changing dependencies or state schema.

```bash
cd /root/ogm-agent-bridge
uv run pytest -q
# Back up state: docs/backup-recovery.md
# Obtain reviewed source revision through normal Git workflow.
uv sync --dev --locked
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest -q
```

Restart harness MCP process. Keep `OGM_STATE_DB` unchanged unless deliberately restoring/migrating state. Check `ogm_health`, then `ogm_list_datasets`.

PyPI/uvx install command is valid only after 0.1.0 publication:

```bash
uvx --from ogm-agent-bridge==0.1.0 ogm-agent-bridge
```

Package is not published/tagged now. Use source setup until release. See [release](release.md).

## Change project/config

Do not reuse state DB across projects. Make named config plus distinct state DB and upload roots. See [configuration](configuration.md). Backup before move. State mappings are project-scoped.

## Uninstall

1. Remove bridge entry from [Claude Code](claude-code.md), [OpenCode](opencode.md), or [Hermes](hermes.md).
2. Stop harness processes.
3. Archive encrypted state backup if memory mappings may be needed.
4. Remove source checkout or package environment.
5. Remove state only after accepting irreversible loss of bridge mappings.

State deletion is irreversible. Core memory/documents remain in core; bridge has no destructive tools and uninstall does not delete remote data.

```bash
rm -rf /root/ogm-agent-bridge
# Only after backup and explicit acceptance:
rm -rf ~/.local/state/ogm-agent-bridge
```

Remove `.env` and backup copies under your secret-handling policy. See [security](security.md) and [backup and recovery](backup-recovery.md).
