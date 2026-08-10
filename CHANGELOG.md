# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.7] - 2026-08-02

### Added

- Rebranded repository, package, and MCP server from `ogm-agent-bridge` to `ogm-mcp-skills`.
- Production-grade `.agents/skills/ogm-mcp-skills/SKILL.md` for autonomous AI coding agents.
- Codebase Knowledge Graph MCP tools (`ogm_search_code_symbols`, `ogm_get_code_call_graph`, `ogm_get_code_chunks`, `ogm_recall_code_memory`, `ogm_record_code_fix`, `ogm_sync_code_file`).
- Ten Agent Memory MCP tools aligned with the OpenGraphMemory core `v0.1.0` source-level HTTP contract.
- Contract coverage for MCP registration, HTTP routes, payloads, redirects, ambiguous writes, and secure uploads.

### Changed

- Rebranded Python package to `ogm_mcp_skills` and CLI entrypoint to `ogm-mcp-skills` / `ogm-mcp`.
- Default permission profile is `read-only`; write and curator capabilities require explicit opt-in.
- All documented `uvx` harness examples pin `ogm-mcp-skills==0.1.7`.
- Upload roots are explicit allowlists and are empty by default.

### Fixed

- Sanitize upstream failures, reject every non-2xx response, correctly classify audited HTTP statuses, and bound safe-request retries.
- Reject non-finite or excessive timeout/retry configuration and malformed or unknown tool arguments.
- Preserve no-retry ambiguous-outcome protection for all write operations, including uploads.
- Validate uploads through descriptor-anchored, symlink-resistant file handling and close every descriptor/response.

### Security

- Raw upstream error details are no longer exposed to MCP callers.
- A missing `OGM_UPLOAD_ROOTS` no longer falls back to exposing the process working directory.

## [0.1.6] - 2026-07-18

### Fixed

- Install the pinned PyPI publisher inside the isolated publish job.

## [0.1.5] - 2026-07-18

### Changed

- Prefer PyPI install and `uvx` usage in README, harness docs, and examples.

### Fixed

- Exclude `SHA256SUMS` from PyPI publish input.
- Align harness example tests with PyPI `uvx` examples.
- Read package version test from `pyproject.toml`.
- Publish to PyPI with `twine==6.1.0` directly.

## [0.1.0] - 2026-07-18

### Added

- Compatibility target: OpenGraphMemory core `7703d3994b49272bef7b0d38caf896cde4338f13`.
- Four graph/community read MCP tools; bridge now exposes eleven tools.
- Query modes `graph_local` and `graph_global`; valid modes are `vector_only`, `graph_only`, `graph_local`, `graph_global`, `hybrid`. No `auto`.
- Query `include_communities` and `community_level` 0..2.
- `.json` upload MIME auto-detection as `application/json`; core validates malformed JSON.
- MCP read and write tools for OpenGraphMemory.
- Claude Code, OpenCode, and Hermes setup docs.
- Typed package marker, package metadata, CI package validation, and tag-gated release workflow.
