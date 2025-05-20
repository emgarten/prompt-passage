"""Asynchronous forwarder that relays chat completions to the upstream API."""

from __future__ import annotations

from typing import Mapping

import httpx

from .config import ModelCfg


class Forwarder:
    """Forwarder with shared :class:`httpx.AsyncClient`."""

    _TIMEOUT = httpx.Timeout(600.0)  # 10 minutes

    def __init__(self, model_map: Mapping[str, ModelCfg]):
        self._model_map = model_map
        self._client = httpx.AsyncClient(timeout=self._TIMEOUT)

    async def aclose(self) -> None:
        """Closes the underlying httpx.AsyncClient."""
        await self._client.aclose()

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    async def forward(
        self,
        endpoint: str,
        body: bytes,
        headers: Mapping[str, str],
    ) -> httpx.Response:
        async def _send() -> httpx.Response:
            return await self._client.post(
                endpoint,
                content=body,
                headers=headers,
            )

        resp = await _send()
        if resp.status_code >= 500:
            resp.close()
            resp = await _send()

        return resp
