"""Asynchronous forwarder that relays chat completions to the upstream API."""

from __future__ import annotations

import asyncio
from typing import Mapping

import httpx

from .config import ModelCfg


class Forwarder:
    """Forwarder with shared :class:`httpx.AsyncClient`."""

    _TIMEOUT = httpx.Timeout(600.0)  # 10 minutes

    def __init__(self, model_map: Mapping[str, ModelCfg]):
        self._model_map = model_map
        self._client = httpx.AsyncClient(timeout=self._TIMEOUT)
        # close client on interpreter shutdown
        asyncio.get_running_loop().create_task(self._aclose_when_done())

    async def _aclose_when_done(self) -> None:  # pragma: no cover
        try:
            await asyncio.Event().wait()  # sleep forever until loop stops
        finally:
            await self._client.aclose()

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    async def forward(
        self,
        model: str,
        body: bytes,
        headers: Mapping[str, str],
    ) -> httpx.Response:
        cfg = self._model_map[model]

        # build outbound headers; copy all except Authorization
        out_headers = {k: v for k, v in headers.items() if k.lower() != "authorization"}
        out_headers["Authorization"] = f"Bearer {cfg.token}"

        async def _send() -> httpx.Response:
            return await self._client.post(
                str(cfg.endpoint),
                content=body,
                headers=out_headers,
            )

        resp = await _send()
        if resp.status_code >= 500:
            resp.close()
            resp = await _send()
        return resp
