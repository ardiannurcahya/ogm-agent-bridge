# Troubleshooting

- Startup failure: set `OGM_BASE_URL`, `OGM_API_KEY`, and UUID `OGM_PROJECT_ID`.
- Health works but graph calls fail auth: verify project key and project ID pair.
- Graph route returns `404`: confirm resource belongs to configured project and entity/relation/evidence ID is correct.
- Validation error: use bounded arguments from [tools](tools.md): path depth max 4, subgraph depth max 2.
- Upload denied: use `personal-safe`; verify path is regular file inside `OGM_UPLOAD_ROOTS`.
- MCP tools absent: confirm absolute bridge path, injected environment, and restart harness.

Run `uv run pytest -q` for local validation.
