from __future__ import annotations

from typing import Dict

import httpx
from fastapi import FastAPI, Request, Response, status
import os
from pathlib import Path
import json

from .config import load_config, ModelCfg
from .forwarder import Forwarder

app = FastAPI(title="OpenAI Chat Proxy", version="1.0.0")

_model_map: Dict[str, "ModelCfg"] = {}
_forwarder: Forwarder | None = None


@app.on_event("startup")
async def _startup() -> None:
    global _model_map, _forwarder  # noqa: PLW0603

    config_path = Path.home() / ".local_llm_proxy" / "config.yaml"
    _model_map = load_config(config_path)
    _forwarder = Forwarder(_model_map)


@app.on_event("shutdown")
async def _shutdown() -> None:
    if _forwarder:
        await _forwarder.aclose()


@app.post("/{model}/chat/completions")
async def chat_proxy(model: str, request: Request) -> Response:
    if model not in _model_map:
        return Response(
            content='{"error": "Unknown model"}',
            media_type="application/json",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    cfg = _model_map[model]
    token = os.getenv(cfg.envKey)
    if not token:
        raise ValueError(f"Environment variable '{cfg.envKey}' not set or empty")

    endpoint = str(cfg.endpoint)

    out_headers = {}
    out_headers["Content-Type"] = "application/json"
    out_headers["Authorization"] = f"Bearer {token}"

    body_bytes = await request.body()
    if body_bytes:
        try:
            # Override the model to match the config
            body_json = json.loads(body_bytes.decode("utf-8"))
            body_json["model"] = model
            body = json.dumps(body_json).encode("utf-8")
        except json.JSONDecodeError:
            body = body_bytes
    else:
        body = body_bytes

    assert _forwarder is not None
    upstream = await _forwarder.forward(endpoint, body, out_headers)

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=dict(upstream.headers),
        media_type=upstream.headers.get("content-type"),
    )


@app.exception_handler(httpx.RequestError)
async def _httpx_error(_: Request, exc: httpx.RequestError) -> Response:
    """Return a generic 502 response on httpx failures."""
    return Response(
        content='{"error": "Upstream failure"}',
        media_type="application/json",
        status_code=status.HTTP_502_BAD_GATEWAY,
    )
