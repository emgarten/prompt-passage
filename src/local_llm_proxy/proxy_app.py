from __future__ import annotations

from typing import Dict

import httpx
from fastapi import FastAPI, Request, Response, status
import os
from pathlib import Path

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


@app.post("/{model}/chat/completions")
async def chat_proxy(model: str, request: Request):  # type: ignore[override]
    if model not in _model_map:
        return Response(
            content='{"error": "Unknown model"}',
            media_type="application/json",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    body = await request.body()
    upstream = await _forwarder.forward(model, body, dict(request.headers))  # type: ignore[arg-type]

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=dict(upstream.headers),
        media_type=upstream.headers.get("content-type"),
    )


@app.exception_handler(httpx.RequestError)
async def _httpx_error(_, exc: httpx.RequestError):  # noqa: D401, ANN001
    return Response(
        content='{"error": "Upstream failure"}',
        media_type="application/json",
        status_code=status.HTTP_502_BAD_GATEWAY,
    )
