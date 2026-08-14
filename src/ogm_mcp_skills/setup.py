"""Automatic Skill and Harness MCP Configuration installer for ogm-mcp-skills."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("ogm_mcp_skills.setup")


def get_embedded_skill_content() -> str:
    """Read the bundled SKILL.md from package resources."""
    resource_path = Path(__file__).parent / "resources" / "SKILL.md"
    if resource_path.exists():
        return resource_path.read_text(encoding="utf-8")
    raise FileNotFoundError(
        f"Embedded SKILL.md resource not found at '{resource_path}'"
    )


def setup_harnesses(
    base_url: str = "http://localhost:8000",
    project_id: str | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Auto-detect and install SKILL.md + MCP config across installed agent harnesses."""
    skill_text = get_embedded_skill_content()
    home = Path.home()
    installed_skills: list[str] = []
    installed_configs: list[str] = []

    # 1. Google Antigravity / Gemini CLI Skill
    antigravity_skill_dir = home / ".gemini" / "config" / "skills" / "ogm"
    try:
        antigravity_skill_dir.mkdir(parents=True, exist_ok=True)
        (antigravity_skill_dir / "SKILL.md").write_text(skill_text, encoding="utf-8")
        installed_skills.append(str(antigravity_skill_dir / "SKILL.md"))
    except Exception as err:
        logger.warning(f"Could not install Antigravity skill: {err}")

    # 2. Antigravity MCP Config
    antigravity_mcp_path = home / ".gemini" / "antigravity-cli" / "mcp_config.json"
    if _merge_mcp_config_json(antigravity_mcp_path, base_url, project_id, api_key):
        installed_configs.append(str(antigravity_mcp_path))

    # 3. Claude Desktop MCP Config (Windows / macOS)
    claude_config_path = (
        home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
        if sys.platform == "win32"
        else home
        / "Library"
        / "Application Support"
        / "Claude"
        / "claude_desktop_config.json"
    )
    if claude_config_path.parent.exists():
        if _merge_mcp_config_json(claude_config_path, base_url, project_id, api_key):
            installed_configs.append(str(claude_config_path))

    return {
        "ok": True,
        "installed_skills": installed_skills,
        "installed_configs": installed_configs,
    }


def _merge_mcp_config_json(
    config_path: Path, base_url: str, project_id: str | None, api_key: str | None
) -> bool:
    """Safely merge ogm MCP server configuration into target JSON file."""
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config: dict[str, Any] = {}
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
            except Exception:
                config = {}

        if "mcpServers" not in config or not isinstance(config["mcpServers"], dict):
            config["mcpServers"] = {}

        env_dict: dict[str, str] = {
            "OGM_BASE_URL": base_url,
            "OGM_PERMISSION_PROFILE": "read-only",
        }
        if project_id:
            env_dict["OGM_PROJECT_ID"] = project_id
        if api_key:
            env_dict["OGM_API_KEY"] = api_key

        config["mcpServers"]["ogm"] = {
            "command": "uvx",
            "args": ["ogm-mcp-skills"],
            "env": env_dict,
        }

        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        return True
    except Exception as err:
        logger.warning(f"Could not merge MCP config into '{config_path}': {err}")
        return False
