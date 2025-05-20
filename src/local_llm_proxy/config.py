"""Configuration loader for the proxy service.

Reads `models.yaml`, validates its structure, and resolves the bearer tokens
for every model from environment variables specified by the `envKey` field.
The result is an immutable mapping that other modules can import at runtime.
"""

from __future__ import annotations

from pathlib import Path
import os
from typing import Dict

import yaml
from pydantic import BaseModel, HttpUrl, ValidationError, field_validator


class ModelCfg(BaseModel):
    """Run-time configuration for a single model entry."""

    endpoint: HttpUrl
    envKey: str
    token: str | None = None  # populated after env lookup

    @field_validator("envKey")
    @classmethod
    def _not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("envKey must not be empty")
        return v

    @field_validator("token", mode="before")
    @classmethod
    def _resolve_token(cls, v, values):  # noqa: ANN001
        if v is not None:
            return v
        key = values.get("envKey")
        token = os.getenv(key)
        if not token:
            raise ValueError(f"Environment variable '{key}' not set or empty")
        return token


def load_config(path: str | Path = "models.yaml") -> Dict[str, ModelCfg]:
    """Parse *path* and return a mapping of model name → :class:`ModelCfg`."""

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("rt", encoding="utf-8") as fp:
        data = yaml.safe_load(fp) or {}

    if not isinstance(data, dict) or "models" not in data:
        raise ValueError("models.yaml must contain a top-level 'models' mapping")

    models: Dict[str, ModelCfg] = {}
    for name, cfg in data["models"].items():
        try:
            models[name] = ModelCfg(**cfg)  # type: ignore[arg-type]
        except ValidationError as exc:
            raise ValueError(f"Invalid config for model '{name}': {exc}") from exc

    if not models:
        raise ValueError("No models configured in models.yaml")

    return models
