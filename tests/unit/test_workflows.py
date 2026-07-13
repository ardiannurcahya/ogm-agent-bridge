"""CI and release workflow policy checks."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
SHA = re.compile(r"^[0-9a-f]{40}$")


def test_workflow_actions_are_full_sha_pins_with_versions() -> None:
    for workflow in WORKFLOWS.glob("*.yml"):
        lines = workflow.read_text().splitlines()
        for index, line in enumerate(lines):
            if "uses: " not in line:
                continue
            pin = line.rsplit("@", 1)[1]
            assert SHA.fullmatch(pin), f"{workflow}:{index + 1}: {pin}"
            assert index > 0 and "v" in lines[index - 1], f"{workflow}:{index + 1}"


def test_release_runs_gates_before_build_and_orders_optional_pypi() -> None:
    release = (WORKFLOWS / "release.yml").read_text()
    for gate in (
        "uv run ruff format --check .",
        "uv run ruff check .",
        "uv run mypy src",
        "uv run pytest -q",
    ):
        assert release.index(gate) < release.index("- run: uv build")
    assert "needs: [build, pypi]" in release
    assert "needs.pypi.result == 'success'" in release


def test_ci_reads_wheel_smoke_version_from_pyproject() -> None:
    ci = (WORKFLOWS / "ci.yml").read_text()
    assert "import tomllib" in ci
    assert '"0.1.0"' not in ci
