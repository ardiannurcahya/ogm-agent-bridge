from pathlib import Path

import pytest

from ogm_agent_bridge.config import ConfigError, load_settings


@pytest.fixture
def env() -> dict[str, str]:
    return {
        "OGM_BASE_URL": "https://api.example.test/",
        "OGM_API_KEY": "secret",
        "OGM_PROJECT_ID": "00000000-0000-0000-0000-000000000001",
    }


def test_loads_required_values_and_defaults(env: dict[str, str]) -> None:
    settings = load_settings(env)

    assert settings.base_url == "https://api.example.test"
    assert settings.timeout_seconds == 30.0
    assert settings.max_retries == 2


def test_loads_dotenv_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OGM_BASE_URL", raising=False)
    monkeypatch.delenv("OGM_API_KEY", raising=False)
    monkeypatch.delenv("OGM_PROJECT_ID", raising=False)
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "OGM_BASE_URL=https://core.test\nOGM_API_KEY=k\nOGM_PROJECT_ID=00000000-0000-0000-0000-000000000001\n"
    )

    assert (
        load_settings(dotenv_path=dotenv).project_id
        == "00000000-0000-0000-0000-000000000001"
    )


def test_rejects_missing_required_value(env: dict[str, str]) -> None:
    del env["OGM_API_KEY"]

    with pytest.raises(ConfigError, match="OGM_API_KEY is required"):
        load_settings(env)


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("OGM_TIMEOUT_SECONDS", "0", "must be positive"),
        ("OGM_MAX_RETRIES", "-1", "must be non-negative"),
    ],
)
def test_rejects_invalid_optional_values(
    env: dict[str, str], name: str, value: str, message: str
) -> None:
    env[name] = value

    with pytest.raises(ConfigError, match=message):
        load_settings(env)
