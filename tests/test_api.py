from pathlib import Path
import importlib
import typing
import httpx

import pytest
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock
import yaml


class GeneratorStream(httpx.AsyncByteStream):
    def __init__(self, gen: typing.AsyncIterator[bytes]) -> None:
        self._gen = gen

    async def __aiter__(self) -> typing.AsyncIterator[bytes]:
        async for chunk in self._gen:
            yield chunk

    async def aclose(self) -> None:
        if hasattr(self._gen, "aclose"):
            await self._gen.aclose()


@pytest.fixture()
def create_config(tmp_path: Path) -> Path:
    cfg_dir = tmp_path / ".prompt_passage"
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


@pytest.fixture()
def create_config_azcli(tmp_path: Path) -> Path:
    cfg_dir = tmp_path / ".prompt_passage"
    cfg_dir.mkdir()
    cfg_file = cfg_dir / "config.yaml"
    cfg_data = {
        "providers": {
            "test-model": {
                "endpoint": "https://mock.upstream/chat/completions",
                "model": "remote-model",
                "auth": {"type": "azcli"},
            }
        }
    }
    cfg_file.write_text(yaml.dump(cfg_data))
    return cfg_file


def test_chat_proxy_success(monkeypatch: pytest.MonkeyPatch, create_config: Path, httpx_mock: HTTPXMock) -> None:
    monkeypatch.setenv("HOME", str(create_config.parent.parent))
    monkeypatch.setenv("TEST_API_KEY_ENV", "secret-token")

    proxy_app = importlib.import_module("prompt_passage.proxy_app")

    httpx_mock.add_response(url="https://mock.upstream/chat/completions", json={"ok": True})

    with TestClient(proxy_app.app) as client:
        resp = client.post(
            "/provider/test-model/chat/completions",
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

    req = httpx_mock.get_requests()[0]
    assert req.headers["Authorization"] == "Bearer secret-token"


def test_chat_proxy_upstream_error(monkeypatch: pytest.MonkeyPatch, create_config: Path, httpx_mock: HTTPXMock) -> None:
    monkeypatch.setenv("HOME", str(create_config.parent.parent))
    monkeypatch.setenv("TEST_API_KEY_ENV", "token")

    proxy_app = importlib.import_module("prompt_passage.proxy_app")

    import httpx

    httpx_mock.add_exception(httpx.ConnectError("boom"))

    with TestClient(proxy_app.app) as client:
        resp = client.post(
            "/provider/test-model/chat/completions",
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
        assert resp.status_code == 502
        assert resp.json() == {"error": "Upstream failure"}


def test_chat_proxy_azcli(monkeypatch: pytest.MonkeyPatch, create_config_azcli: Path, httpx_mock: HTTPXMock) -> None:
    monkeypatch.setenv("HOME", str(create_config_azcli.parent.parent))

    token_obj = type("Tok", (), {"token": "cli-token"})()

    class DummyCred:
        def get_token(self, scope: str) -> object:
            assert scope == "https://cognitiveservices.azure.com/.default"
            return token_obj

    proxy_app = importlib.import_module("prompt_passage.proxy_app")
    monkeypatch.setattr("prompt_passage.auth_providers.AzureCliCredential", lambda: DummyCred())

    httpx_mock.add_response(url="https://mock.upstream/chat/completions", json={"ok": True})

    with TestClient(proxy_app.app) as client:
        resp = client.post(
            "/provider/test-model/chat/completions",
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
        assert resp.status_code == 200

    req = httpx_mock.get_requests()[0]
    assert req.headers["Authorization"] == "Bearer cli-token"


def test_chat_proxy_stream(monkeypatch: pytest.MonkeyPatch, create_config: Path, httpx_mock: HTTPXMock) -> None:
    monkeypatch.setenv("HOME", str(create_config.parent.parent))
    monkeypatch.setenv("TEST_API_KEY_ENV", "tok")

    proxy_app = importlib.import_module("prompt_passage.proxy_app")

    async def gen() -> typing.AsyncIterator[bytes]:
        yield b'data: {"id":1}\n\n'
        yield b"data: [DONE]\n\n"

    stream = GeneratorStream(gen())
    httpx_mock.add_response(
        url="https://mock.upstream/chat/completions",
        headers={"content-type": "text/event-stream"},
        stream=stream,
    )

    with TestClient(proxy_app.app) as client:
        with client.stream(
            "POST",
            "/provider/test-model/chat/completions",
            json={"messages": [{"role": "user", "content": "hi"}], "stream": True},
        ) as resp:
            chunks = list(resp.iter_bytes())

    assert b"data: {" in chunks[0]


def test_chat_proxy_unknown_provider(monkeypatch: pytest.MonkeyPatch, create_config: Path) -> None:
    monkeypatch.setenv("HOME", str(create_config.parent.parent))
    monkeypatch.setenv("TEST_API_KEY_ENV", "tok")

    proxy_app = importlib.import_module("prompt_passage.proxy_app")

    with TestClient(proxy_app.app) as client:
        resp = client.post(
            "/provider/missing/chat/completions",
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
        assert resp.status_code == 404
        assert resp.json() == {"error": "Unknown provider"}


def test_chat_proxy_upstream_500(monkeypatch: pytest.MonkeyPatch, create_config: Path, httpx_mock: HTTPXMock) -> None:
    monkeypatch.setenv("HOME", str(create_config.parent.parent))
    monkeypatch.setenv("TEST_API_KEY_ENV", "tok")

    proxy_app = importlib.import_module("prompt_passage.proxy_app")

    httpx_mock.add_response(status_code=500, json={"err": 1})
    httpx_mock.add_response(status_code=500, json={"err": 1})

    with TestClient(proxy_app.app) as client:
        resp = client.post(
            "/provider/test-model/chat/completions",
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
        assert resp.status_code == 500


def test_chat_proxy_stream_upstream_error(
    monkeypatch: pytest.MonkeyPatch, create_config: Path, httpx_mock: HTTPXMock
) -> None:
    monkeypatch.setenv("HOME", str(create_config.parent.parent))
    monkeypatch.setenv("TEST_API_KEY_ENV", "tok")

    proxy_app = importlib.import_module("prompt_passage.proxy_app")

    httpx_mock.add_exception(httpx.ConnectError("fail"))

    with TestClient(proxy_app.app) as client:
        resp = client.post(
            "/provider/test-model/chat/completions",
            json={"messages": [{"role": "user", "content": "hi"}], "stream": True},
        )
        assert resp.status_code == 502
        assert resp.json() == {"error": "Upstream failure"}


def test_chat_proxy_stream_500(monkeypatch: pytest.MonkeyPatch, create_config: Path, httpx_mock: HTTPXMock) -> None:
    monkeypatch.setenv("HOME", str(create_config.parent.parent))
    monkeypatch.setenv("TEST_API_KEY_ENV", "tok")

    proxy_app = importlib.import_module("prompt_passage.proxy_app")

    def make_stream() -> GeneratorStream:
        async def gen() -> typing.AsyncIterator[bytes]:
            yield b"oops"

        return GeneratorStream(gen())

    httpx_mock.add_response(status_code=500, headers={"content-type": "text/event-stream"}, stream=make_stream())
    httpx_mock.add_response(status_code=500, headers={"content-type": "text/event-stream"}, stream=make_stream())

    with TestClient(proxy_app.app) as client:
        with client.stream(
            "POST",
            "/provider/test-model/chat/completions",
            json={"messages": [{"role": "user", "content": "hi"}], "stream": True},
        ) as resp:
            list(resp.iter_bytes())

        assert resp.status_code == 500
