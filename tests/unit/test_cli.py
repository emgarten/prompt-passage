import importlib
from pathlib import Path
import yaml
import pytest


def _create_basic_config(path: Path) -> None:
    cfg = {
        "providers": {
            "p": {
                "endpoint": "https://example.com",
                "model": "m",
                "auth": {"type": "apikey", "key": "k"},
            }
        }
    }
    path.write_text(yaml.dump(cfg))


def test_cli_https_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg = tmp_path / ".prompt-passage.yaml"
    _create_basic_config(cfg)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PROMPT_PASSAGE_CERTFILE", "/c.pem")
    monkeypatch.setenv("PROMPT_PASSAGE_KEYFILE", "/k.pem")
    monkeypatch.setenv("PROMPT_PASSAGE_CA_CERTS", "/ca.pem")

    called = {}

    def dummy_run(*args: object, **kwargs: object) -> None:
        called.update(kwargs)

    cli = importlib.import_module("prompt_passage.cli")
    monkeypatch.setattr(cli.uvicorn, "run", dummy_run)
    monkeypatch.setattr("sys.argv", ["prog"])  # clear pytest args

    cli.main()

    assert called.get("ssl_certfile") == "/c.pem"
    assert called.get("ssl_keyfile") == "/k.pem"
    assert called.get("ssl_ca_certs") == "/ca.pem"


def test_cli_no_https(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg = tmp_path / ".prompt-passage.yaml"
    _create_basic_config(cfg)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("PROMPT_PASSAGE_CERTFILE", raising=False)
    monkeypatch.delenv("PROMPT_PASSAGE_KEYFILE", raising=False)
    monkeypatch.delenv("PROMPT_PASSAGE_CA_CERTS", raising=False)

    called = {}

    def dummy_run(*args: object, **kwargs: object) -> None:
        called.update(kwargs)

    cli = importlib.import_module("prompt_passage.cli")
    monkeypatch.setattr(cli.uvicorn, "run", dummy_run)
    monkeypatch.setattr("sys.argv", ["prog"])  # clear pytest args

    cli.main()

    assert "ssl_certfile" not in called
    assert "ssl_keyfile" not in called
    assert "ssl_ca_certs" not in called


def test_cli_partial_https(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg = tmp_path / ".prompt-passage.yaml"
    _create_basic_config(cfg)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PROMPT_PASSAGE_CERTFILE", "/c.pem")
    monkeypatch.delenv("PROMPT_PASSAGE_KEYFILE", raising=False)
    monkeypatch.delenv("PROMPT_PASSAGE_CA_CERTS", raising=False)

    called = {}

    def dummy_run(*args: object, **kwargs: object) -> None:
        called.update(kwargs)

    cli = importlib.import_module("prompt_passage.cli")
    monkeypatch.setattr(cli.uvicorn, "run", dummy_run)
    monkeypatch.setattr("sys.argv", ["prog"])  # clear pytest args

    cli.main()

    assert called.get("ssl_certfile") == "/c.pem"
    assert "ssl_keyfile" not in called
    assert "ssl_ca_certs" not in called
