# Prompt Passage

A local proxy for LLMs, providing a unified interface for multiple models and support for identity based authentication.

## Example config

```yaml
service:
  port: 8095
  auth:
    type: apikey
    key: localkey
providers:
  azure-o4-mini-env:
    endpoint: "https://{service}.cognitiveservices.azure.com/openai/deployments/o4-mini/chat/completions?api-version=2025-01-01-preview"
    model: o4-mini
    auth:
      type: apikey
      envKey: AZURE_OPENAI_API_KEY
  azure-o4-mini-key:
    endpoint: "https://{service}.cognitiveservices.azure.com/openai/deployments/o4-mini/chat/completions?api-version=2025-01-01-preview"
    model: o4-mini
    auth:
      type: apikey
      key: djjskskskkkk
  azure-o4-mini-azcli:
    endpoint: "https://{service}.cognitiveservices.azure.com/openai/deployments/o4-mini/chat/completions?api-version=2025-01-01-preview"
    model: o4-mini
    auth:
      type: azcli
```

## Dev environment setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install packages
make install

# Lint and type check
make check
```