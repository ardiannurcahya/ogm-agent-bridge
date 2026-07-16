"""Documentation consistency checks."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"

REQUIRED_DOCS = {
    "configuration.md",
    "tools.md",
    "session-lifecycle.md",
    "security.md",
    "backup-recovery.md",
    "troubleshooting.md",
    "resource-guidance.md",
    "upgrade-uninstall.md",
}
TOOLS = {
    "ogm_health",
    "ogm_list_datasets",
    "ogm_query",
    "ogm_graph_explorer",
    "ogm_list_community_reports",
    "ogm_get_community_report",
    "ogm_list_community_report_jobs",
    "ogm_search_memory",
    "ogm_create_session",
    "ogm_remember",
    "ogm_upload_document",
}
ENV_DEFAULTS = {
    "OGM_TIMEOUT_SECONDS": "30",
    "OGM_MAX_RETRIES": "2",
    "OGM_STATE_DB": "~/.local/state/ogm-agent-bridge/state.db",
    "OGM_PERMISSION_PROFILE": "personal-safe",
}


def test_required_docs_exist() -> None:
    assert REQUIRED_DOCS <= {path.name for path in DOCS.glob("*.md")}


def test_markdown_links_resolve() -> None:
    for path in [ROOT / "README.md", *DOCS.glob("*.md")]:
        text = path.read_text()
        for target in re.findall(r"\[[^]]+\]\(([^)#]+)(?:#[^)]*)?\)", text):
            if "://" not in target and not target.startswith("mailto:"):
                assert (path.parent / target).resolve().exists(), f"{path}: {target}"


def test_environment_defaults_match_example_and_docs() -> None:
    example = (ROOT / ".env.example").read_text()
    config = (DOCS / "configuration.md").read_text()
    for name, value in ENV_DEFAULTS.items():
        assert f"{name}={value}" in example
        assert value in config
    assert "full" not in example
    assert "No `full` profile" in config


def test_tool_docs_match_current_seven_tools() -> None:
    tools_doc = (DOCS / "tools.md").read_text()
    server = (ROOT / "src/ogm_agent_bridge/mcp_server.py").read_text()
    documented = set(re.findall(r"## `(ogm_[a-z_]+)`", tools_doc))
    registered = set(re.findall(r"async def (ogm_[a-z_]+)\(", server))
    assert documented == TOOLS
    assert registered == TOOLS


def test_no_stale_session_or_upload_claims() -> None:
    text = "\n".join(
        path.read_text() for path in [ROOT / "README.md", *DOCS.glob("*.md")]
    )
    assert "local `path`" in text
    assert "B1 query currently accepts core IDs directly" in text
    assert "B2 mapping is only resolved by remember" in text
    assert "bridge `session_id` is not" in text
