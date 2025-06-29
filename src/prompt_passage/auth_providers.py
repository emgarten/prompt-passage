from __future__ import annotations

from abc import ABC, abstractmethod

from azure.identity import DefaultAzureCredential
from azure.core.credentials import AccessToken


class TokenProvider(ABC):
    """Abstract base class for retrieving bearer tokens."""

    @abstractmethod
    def get_token(self) -> str:
        """Return a bearer token string."""
        raise NotImplementedError


class ApiKeyProvider(TokenProvider):
    """Simple provider that returns a static API key."""

    def __init__(self, key: str):
        self._key = key

    def get_token(self) -> str:  # noqa: D401 - simple return
        """Return the stored API key."""
        return self._key


class AzureCliProvider(TokenProvider):
    """Provider that fetches a token from Azure CLI credentials."""

    _SCOPE = "https://cognitiveservices.azure.com/.default"

    def __init__(self) -> None:
        self._credential = DefaultAzureCredential()

    def get_token(self) -> str:
        access_token: AccessToken = self._credential.get_token(self._SCOPE)
        return access_token.token
