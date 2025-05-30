# local-llm-proxy

Proxy local LLM calls to Azure


## Example config

```yaml
defaults:
  provider: azure-o4-mini-env
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

When using `azcli` authentication the proxy retrieves a bearer token from the
Azure CLI credentials (for example acquired via `az login`).

## Dev environment setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install packages
make install

# Lint and type check
make check
```