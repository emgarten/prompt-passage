from __future__ import annotations

from typing import Dict

import httpx
import logging
from uvicorn.logging import DefaultFormatter
from fastapi import FastAPI, Request, Response, status
from pathlib import Path
import json

from .config import load_config, ProviderCfg
from .forwarder import Forwarder

_handler = logging.StreamHandler()
_handler.setFormatter(DefaultFormatter(fmt="%(levelprefix)s %(message)s", use_colors=True))
_root = logging.getLogger()
_root.handlers.clear()
_root.addHandler(_handler)
_root.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


def _pretty(data: bytes) -> str:
    """Return a prettified string representation of *data* if it's JSON."""
    try:
        obj = json.loads(data.decode("utf-8"))
    except Exception:
        return data.decode("utf-8", errors="replace")
    return json.dumps(obj, indent=2, ensure_ascii=False)


app = FastAPI(title="OpenAI Chat Proxy", version="1.0.0")

_model_map: Dict[str, ProviderCfg] = {}
_forwarder: Forwarder | None = None


@app.on_event("startup")
async def _startup() -> None:
    global _model_map, _forwarder  # noqa: PLW0603

    config_path = Path.home() / ".local_llm_proxy" / "config.yaml"
    _model_map = load_config(config_path).providers
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
    token = cfg.token_provider.get_token()

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

    logger.info("Forwarding request to %s", endpoint)
    logger.info("Outgoing body:\n%s", _pretty(body))

    assert _forwarder is not None
    try:
        upstream = await _forwarder.forward(endpoint, body, out_headers)
    except httpx.RequestError as exc:
        logger.exception("Failed to reach upstream: %s", exc)
        raise

    resp_pretty = _pretty(upstream.content)
    logger.info("Upstream response (%s):\n%s", upstream.status_code, resp_pretty)
    try:
        usage = json.loads(upstream.content.decode("utf-8")).get("usage")
    except Exception:
        usage = None
    if usage is not None:
        logger.info("Usage results: %s", usage)

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=dict(upstream.headers),
        media_type=upstream.headers.get("content-type"),
    )


@app.exception_handler(httpx.RequestError)
async def _httpx_error(_: Request, exc: httpx.RequestError) -> Response:
    """Return a generic 502 response on httpx failures."""
    logger.error("Upstream request error: %s", exc)
    return Response(
        content='{"error": "Upstream failure"}',
        media_type="application/json",
        status_code=status.HTTP_502_BAD_GATEWAY,
    )
