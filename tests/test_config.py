from pathlib import Path

import pytest
from pydantic import ValidationError

from prompt_passage.config import load_config, parse_config
from prompt_passage.auth_providers import ApiKeyProvider, AzureCliProvider


def test_load_config_file_not_found(tmp_path: Path) -> None:
    """Test FileNotFoundError when config file does not exist."""
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "non_existent.yaml")


def test_parse_config_valid_env_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """A valid config resolves an API key from the environment."""
    monkeypatch.setenv("TEST_ENV_KEY", "abc123")
    raw = {
        "providers": {
            "p1": {
                "endpoint": "https://example.com",
                "model": "m",
                "auth": {"type": "apikey", "envKey": "TEST_ENV_KEY"},
            }
        }
    }
    cfg = parse_config(raw)
    assert cfg.providers["p1"].auth.api_key == "abc123"


def test_parse_config_missing_default_provider() -> None:
    """Defaults referencing unknown providers should fail validation."""
    raw = {
        "defaults": {"provider": "missing"},
        "providers": {
            "p1": {
                "endpoint": "https://example.com",
                "model": "m",
                "auth": {"type": "apikey", "key": "k"},
            }
        },
    }
    with pytest.raises(ValidationError):
        parse_config(raw)


def test_parse_config_providers_empty() -> None:
    """Configuration must contain at least one provider."""
    with pytest.raises(ValidationError):
        parse_config({"providers": {}})


def test_parse_config_apikey_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """An apikey auth entry without key or envKey should fail."""
    monkeypatch.delenv("MISSING", raising=False)
    raw = {
        "providers": {
            "p1": {
                "endpoint": "https://example.com",
                "model": "m",
                "auth": {"type": "apikey", "envKey": "MISSING"},
            }
        }
    }
    with pytest.raises(ValidationError):
        parse_config(raw)


def test_parse_config_azcli_returns_none() -> None:
    """Auth of type azcli should not resolve an API key."""
    raw = {
        "providers": {
            "p1": {
                "endpoint": "https://example.com",
                "model": "m",
                "auth": {"type": "azcli"},
            }
        }
    }
    cfg = parse_config(raw)
    prov = cfg.providers["p1"].auth
    assert prov.api_key is None
    assert isinstance(prov.provider, AzureCliProvider)


def test_parse_config_apikey_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "x")
    raw = {
        "providers": {
            "p1": {
                "endpoint": "https://example.com",
                "model": "m",
                "auth": {"type": "apikey", "envKey": "ENV"},
            }
        }
    }
    cfg = parse_config(raw)
    auth = cfg.providers["p1"].auth
    assert isinstance(auth.provider, ApiKeyProvider)
