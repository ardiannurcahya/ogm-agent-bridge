# Upgrade And Uninstall

For source upgrade, stop harness, update checkout, run `uv sync --dev --locked`, then run format, lint, typecheck, and tests. Restart harness and call `ogm_health` then `ogm_list_datasets`.

Bridge is stateless. Uninstall removes harness MCP config, source checkout, and local `.env` according to secret policy. It does not delete core data.
