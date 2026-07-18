# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.3] - 2026-07-18

### Changed

- Prefer PyPI install and `uvx` usage in README, harness docs, and examples.

### Fixed

- Exclude `SHA256SUMS` from PyPI publish input.
- Align harness example tests with PyPI `uvx` examples.

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
