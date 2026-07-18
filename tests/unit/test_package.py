import tomllib
from pathlib import Path

from ogm_agent_bridge import __version__


def test_package_has_version() -> None:
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    project = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]
    assert __version__.count(".") == 2
    assert project["version"].count(".") == 2
