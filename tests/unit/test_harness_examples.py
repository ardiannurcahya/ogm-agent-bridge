"""B3 adapter example conformance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_ENV = {
    "OGM_BASE_URL",
    "OGM_API_KEY",
    "OGM_PROJECT_ID",
    "OGM_PERMISSION_PROFILE",
}
EXPECTED_TOOLS = {
    "ogm_health",
    "ogm_list_datasets",
    "ogm_search_entities",
    "ogm_get_entity",
    "ogm_get_neighbors",
    "ogm_find_path",
    "ogm_get_subgraph",
    "ogm_get_graph",
    "ogm_get_evidence",
    "ogm_get_relation_evidence",
    "ogm_upload_document",
}


def test_claude_example_is_valid_and_complete() -> None:
    example = _json_example("examples/claude-code/.mcp.json.example")
    server = example["mcpServers"]["ogm"]

    assert server["command"] == "uvx"
    assert server["args"] == ["ogm-agent-bridge"]
    assert set(server["env"]) == REQUIRED_ENV
    assert set(server["env"].values()) == {f"${{{name}}}" for name in REQUIRED_ENV}


def test_opencode_example_is_valid_and_complete() -> None:
    example = _json_example("examples/opencode/opencode.json.example")
    server = example["mcp"]["ogm"]

    assert example["$schema"] == "https://opencode.ai/config.json"
    assert server["type"] == "local"
    assert server["command"] == ["uvx", "ogm-agent-bridge"]
    assert server["enabled"] is True
    assert set(server["environment"]) == REQUIRED_ENV
    assert set(server["environment"].values()) == {
        f"{{env:{name}}}" for name in REQUIRED_ENV
    }


def test_hermes_example_declares_explicit_bridge_environment() -> None:
    example = _simple_yaml(_text("examples/hermes/config.yaml.example"))
    server = example["mcp_servers"]["ogm"]

    assert server["command"] == "uvx"
    assert server["args"] == ["ogm-agent-bridge"]
    assert server["env"] == {name: f"${{{name}}}" for name in REQUIRED_ENV}
    assert server["timeout"] == 120
    assert server["connect_timeout"] == 60


def test_harness_docs_state_tool_expectation_and_safe_setup() -> None:
    for path in ("docs/claude-code.md", "docs/opencode.md", "docs/hermes.md"):
        content = _text(path)
        assert "/absolute/path/ogm-agent-bridge" in content
        assert "OGM_PERMISSION_PROFILE" in content
        assert "11 tools" in content
        assert "read-only" in content
        for tool in EXPECTED_TOOLS:
            assert tool in content


def _json_example(path: str) -> dict[str, Any]:
    return json.loads(_text(path))


def _simple_yaml(content: str) -> dict[str, Any]:
    """Parse required small YAML mapping/list subset without PyYAML."""
    result: dict[str, Any] = {"mcp_servers": {"ogm": {}}}
    server = result["mcp_servers"]["ogm"]
    section: str | None = None
    for raw_line in content.splitlines():
        text = raw_line.strip()
        if not text or text.startswith("#") or text in {"mcp_servers:", "ogm:"}:
            continue
        if text.startswith("- "):
            assert section == "args"
            server["args"].append(_yaml_scalar(text[2:]))
            continue
        key, value = text.split(":", 1)
        if not value.strip():
            assert key in {"args", "env", "tools"}
            section = key
            server[key] = [] if key == "args" else {}
            continue
        if section in {"env", "tools"} and raw_line.startswith("      "):
            server[section][key] = _yaml_scalar(value.strip())
        else:
            section = None
            server[key] = _yaml_scalar(value.strip())
    return result


def _yaml_scalar(value: str) -> str | int:
    value = value.strip('"')
    return int(value) if value.isdigit() else value


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")
