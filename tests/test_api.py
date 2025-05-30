from pathlib import Path
import importlib

import pytest
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock
import yaml

import local_llm_proxy.config as cfg

cfg.ModelCfg = cfg.ProviderCfg


@pytest.fixture()
def create_config(tmp_path: Path) -> Path:
    cfg_dir = tmp_path / ".local_llm_proxy"
    cfg_dir.mkdir()
    cfg_file = cfg_dir / "config.yaml"
    cfg_data = {
        "providers": {
            "test-model": {
                "endpoint": "https://mock.upstream/chat/completions",
                "model": "remote-model",
                "auth": {
                    "type": "apikey",
                    "envKey": "TEST_API_KEY_ENV",
                },
            }
        }
    }
    cfg_file.write_text(yaml.dump(cfg_data))
    return cfg_file


def _load_providers(path: str | Path) -> dict[str, cfg.ProviderCfg]:
    providers = cfg.load_config(path).providers
    for p in providers.values():
        # Provide backward-compat attribute expected by proxy_app
        object.__setattr__(p, "envKey", p.auth.envKey)
    return providers  # type: ignore[no-any-return]


def test_chat_proxy_success(monkeypatch: pytest.MonkeyPatch, create_config: Path, httpx_mock: HTTPXMock) -> None:
    monkeypatch.setenv("HOME", str(create_config.parent.parent))
    monkeypatch.setenv("TEST_API_KEY_ENV", "secret-token")

    proxy_app = importlib.import_module("local_llm_proxy.proxy_app")
    monkeypatch.setattr(proxy_app, "load_config", _load_providers)

    httpx_mock.add_response(url="https://mock.upstream/chat/completions", json={"ok": True})

    with TestClient(proxy_app.app) as client:
        resp = client.post(
            "/test-model/chat/completions",
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

    req = httpx_mock.get_requests()[0]
    assert req.headers["Authorization"] == "Bearer secret-token"


def test_chat_proxy_upstream_error(monkeypatch: pytest.MonkeyPatch, create_config: Path, httpx_mock: HTTPXMock) -> None:
    monkeypatch.setenv("HOME", str(create_config.parent.parent))
    monkeypatch.setenv("TEST_API_KEY_ENV", "token")

    proxy_app = importlib.import_module("local_llm_proxy.proxy_app")
    monkeypatch.setattr(proxy_app, "load_config", _load_providers)

    import httpx

    httpx_mock.add_exception(httpx.ConnectError("boom"))

    with TestClient(proxy_app.app) as client:
        resp = client.post(
            "/test-model/chat/completions",
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
        assert resp.status_code == 502
        assert resp.json() == {"error": "Upstream failure"}
