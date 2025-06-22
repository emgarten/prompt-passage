"""Asynchronous forwarder that relays chat completions to the upstream API."""

from __future__ import annotations

from typing import Mapping

import httpx

from .config import ProviderCfg


class Forwarder:
    """Forwarder with shared :class:`httpx.AsyncClient`."""

    _TIMEOUT = httpx.Timeout(600.0)  # 10 minutes

    def __init__(self, model_map: Mapping[str, ProviderCfg]):
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
            await resp.aclose()
            resp = await _send()

        return resp

    async def stream(
        self,
        endpoint: str,
        body: bytes,
        headers: Mapping[str, str],
    ) -> httpx.Response:
        """Send a POST request and return a streaming ``httpx.Response``."""

        request = self._client.build_request("POST", endpoint, content=body, headers=headers)

        resp = await self._client.send(request, stream=True)
        if resp.status_code >= 500:
            await resp.aclose()
            resp = await self._client.send(request, stream=True)

        return resp
