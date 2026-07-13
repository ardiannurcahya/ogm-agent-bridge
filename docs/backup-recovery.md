# Backup and recovery

Bridge state SQLite maps bridge session IDs to core IDs and tracks identity provisioning. Core lacks public lookup/list routes needed for reliable reconstruction. Back up state before upgrades, host migration, or changing state path.

## Secure backup

Stop harness/bridge first. SQLite backup must capture consistent database. Use SQLite online backup, not blind copy during writes.

```bash
umask 077
mkdir -p ~/.local/state/ogm-agent-bridge/backups
sqlite3 ~/.local/state/ogm-agent-bridge/state.db ".backup '~/.local/state/ogm-agent-bridge/backups/state-$(date +%F).db'"
chmod 600 ~/.local/state/ogm-agent-bridge/backups/state-*.db
```

Keep backup outside upload roots. Encrypt before off-host storage. Test restore on copy, never production state.

```bash
umask 077
cp ~/.local/state/ogm-agent-bridge/backups/state-YYYY-MM-DD.db /tmp/ogm-state-restore-check.db
sqlite3 /tmp/ogm-state-restore-check.db "PRAGMA integrity_check;"
rm /tmp/ogm-state-restore-check.db
```

## Restore

1. Stop all harnesses using target state DB.
2. Preserve failed state copy for investigation.
3. Replace state file from verified backup with owner-only permissions.
4. Restart bridge and call read tools.
5. Use known bridge session only for `ogm_remember` after verifying expected mapping and no ambiguous prior write.

```bash
umask 077
cp ~/.local/state/ogm-agent-bridge/state.db ~/.local/state/ogm-agent-bridge/state.before-restore.db
cp ~/.local/state/ogm-agent-bridge/backups/state-YYYY-MM-DD.db ~/.local/state/ogm-agent-bridge/state.db
chmod 600 ~/.local/state/ogm-agent-bridge/state.db
```

## Ambiguous write recovery

`ogm_remember` timeout, transport failure, or ambiguous upstream failure means core may have accepted message/fact. Bridge blocks later writes for that bridge session.

1. Do not retry `ogm_remember`.
2. Preserve SQLite file and stderr diagnostics without secrets.
3. Inspect core through approved operator tooling for expected message/fact.
4. Decide recorded outcome: accepted once, or not accepted.
5. Repair/replace local state only after confirmed outcome. No bridge repair command exists.
6. Resume writes only after operator confirms mapping and duplicate risk resolved.

## State-loss limitation

Do not delete state to fix session problem. Lost state prevents reliable recovery of core user, agent, and session IDs because public core API lacks required lookup/list routes. Bridge cannot safely recreate identities. Restore known backup. Without backup, treat old mappings as unrecoverable and use controlled operator investigation; do not claim automatic recovery.

Related: [session lifecycle](session-lifecycle.md), [security](security.md), [troubleshooting](troubleshooting.md).
