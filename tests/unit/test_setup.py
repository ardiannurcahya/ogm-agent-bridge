"""Unit tests for ogm_mcp_skills.setup module."""

from __future__ import annotations

from pathlib import Path

from ogm_mcp_skills.setup import get_embedded_skill_content, setup_harnesses


def test_get_embedded_skill_content() -> None:
    content = get_embedded_skill_content()
    assert "OpenGraphMemory (OGM) Skill" in content
    assert "ogm_index_codebase" in content


def test_setup_harnesses(tmp_path: Path, monkeypatch: any) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    res = setup_harnesses("http://localhost:8000", "test_proj", "test_key")
    assert res["ok"] is True
    skill_file = tmp_path / ".gemini" / "config" / "skills" / "ogm" / "SKILL.md"
    assert skill_file.exists()
    assert "OpenGraphMemory (OGM) Skill" in skill_file.read_text(encoding="utf-8")
    mcp_file = tmp_path / ".gemini" / "antigravity-cli" / "mcp_config.json"
    assert mcp_file.exists()
    assert "mcpServers" in mcp_file.read_text(encoding="utf-8")
