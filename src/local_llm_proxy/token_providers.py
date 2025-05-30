from __future__ import annotations

from abc import ABC, abstractmethod

from typing import cast

from azure.identity.aio import AzureCliCredential
from azure.core.credentials import AccessToken


class TokenProvider(ABC):
    """Abstract provider interface for acquiring bearer tokens."""

    async def aclose(self) -> None:  # pragma: no cover - default noop
        """Clean up resources for the provider."""
        return None

    @abstractmethod
    async def get_token(self) -> str:
        """Return a bearer token for authenticating upstream calls."""
        raise NotImplementedError


class ApiKeyProvider(TokenProvider):
    """Simple token provider that returns a pre-resolved API key."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def get_token(self) -> str:  # pragma: no cover - trivial
        return self._api_key


class AzCliTokenProvider(TokenProvider):
    """Token provider that uses Azure CLI credentials."""

    def __init__(self, scope: str = "https://cognitiveservices.azure.com/.default") -> None:
        self._credential = AzureCliCredential()
        self._scope = scope

    async def get_token(self) -> str:
        token = await self._credential.get_token(self._scope)
        return cast(AccessToken, token).token

    async def aclose(self) -> None:
        await self._credential.close()
