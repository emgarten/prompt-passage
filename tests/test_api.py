from pathlib import Path
import importlib
import types

import pytest
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock
import yaml

import local_llm_proxy.config as cfg

# These functional tests expect the proxy to accept a mapping of ProviderCfg
# objects rather than ModelCfg instances. Patch this during each test using the
# monkeypatch fixture to avoid side effects on other modules.


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


class _DummyProvider:
    def __init__(self, token: str) -> None:
        self._token = token

    async def get_token(self) -> str:
        return self._token

    async def aclose(self) -> None:
        return None


def _build_model_map(config: cfg.RootConfig) -> dict[str, object]:
    result = {}
    for name, p in config.providers.items():
        object.__setattr__(p, "envKey", p.auth.envKey)
        token = p.auth.api_key or "token"
        result[name] = types.SimpleNamespace(
            endpoint=p.endpoint,
            model=p.model,
            token_provider=_DummyProvider(token),
        )
    return result


def test_chat_proxy_success(monkeypatch: pytest.MonkeyPatch, create_config: Path, httpx_mock: HTTPXMock) -> None:
    monkeypatch.setenv("HOME", str(create_config.parent.parent))
    monkeypatch.setenv("TEST_API_KEY_ENV", "secret-token")

    proxy_app = importlib.import_module("local_llm_proxy.proxy_app")
    monkeypatch.setattr(cfg, "ModelCfg", cfg.ProviderCfg)
    monkeypatch.setattr(proxy_app, "build_model_map", _build_model_map)
    async def _noop() -> None:
        return None
    monkeypatch.setattr(proxy_app, "_shutdown", _noop)

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
    monkeypatch.setattr(cfg, "ModelCfg", cfg.ProviderCfg)
    monkeypatch.setattr(proxy_app, "build_model_map", _build_model_map)
    async def _noop() -> None:
        return None
    monkeypatch.setattr(proxy_app, "_shutdown", _noop)

    import httpx

    httpx_mock.add_exception(httpx.ConnectError("boom"))

    with TestClient(proxy_app.app) as client:
        resp = client.post(
            "/test-model/chat/completions",
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
        assert resp.status_code == 502
        assert resp.json() == {"error": "Upstream failure"}
