"""Documentation consistency checks."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"

REQUIRED_DOCS = {
    "configuration.md",
    "tools.md",
    "security.md",
    "troubleshooting.md",
    "resource-guidance.md",
    "upgrade-uninstall.md",
}
TOOLS = {
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
    "ogm_memory_list_episodes",
    "ogm_memory_get_episode",
    "ogm_memory_search",
    "ogm_memory_create_episode",
    "ogm_memory_append_attempt",
    "ogm_memory_record_outcome",
    "ogm_memory_feedback_episode",
    "ogm_memory_supersede_episode",
    "ogm_memory_feedback_pattern",
    "ogm_memory_supersede_pattern",
}
ENV_DEFAULTS = {
    "OGM_TIMEOUT_SECONDS": "30",
    "OGM_MAX_RETRIES": "2",
    "OGM_PERMISSION_PROFILE": "personal-safe",
}


def test_required_docs_exist() -> None:
    assert REQUIRED_DOCS <= {path.name for path in DOCS.glob("*.md")}


def test_markdown_links_resolve() -> None:
    for path in [ROOT / "README.md", *DOCS.glob("*.md")]:
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^]]+\]\(([^)#]+)(?:#[^)]*)?\)", text):
            if "://" not in target and not target.startswith("mailto:"):
                assert (path.parent / target).resolve().exists(), f"{path}: {target}"


def test_environment_defaults_match_example_and_docs() -> None:
    example = (ROOT / ".env.example").read_text(encoding="utf-8")
    config = (DOCS / "configuration.md").read_text(encoding="utf-8")
    for name, value in ENV_DEFAULTS.items():
        assert f"{name}={value}" in example
        assert value in config
    assert "full" not in example
    assert "No full profile" in config


def test_tool_docs_match_current_tools() -> None:
    tools_doc = (DOCS / "tools.md").read_text(encoding="utf-8")
    server = (ROOT / "src/ogm_agent_bridge/mcp_server.py").read_text(encoding="utf-8")
    documented = set(re.findall(r"## `(ogm_[a-z_]+)`", tools_doc))
    registered = set(re.findall(r"async def (ogm_[a-z_]+)\(", server))
    assert documented == TOOLS
    assert registered == TOOLS


def test_docs_are_stateless_graph_first() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [ROOT / "README.md", *DOCS.glob("*.md")]
    )
    assert "OGM_UPLOAD_ROOTS" in text
    assert "ogm_search_entities" in text
    assert "OGM_STATE_DB" not in text
    assert "ogm_create_session" not in text
    assert "automatic conversation ingestion" in text
