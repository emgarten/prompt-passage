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
## Docker

Build the container image:

```bash
docker build -t prompt-passage .
```

Run the proxy with your configuration file mounted:

```bash
docker run -p 8095:8095 \
  -v $(pwd)/models.yaml:/etc/prompt-passage.yaml \
  prompt-passage
```

When using the `azcli` authentication method, mount your Azure CLI credentials directory:

```bash
docker run -p 8095:8095 \
  -v $(pwd)/models.yaml:/etc/prompt-passage.yaml \
  -v ~/.azure:/root/.azure \
  prompt-passage
```

The container automatically executes `llm-proxy` and reads its configuration from `/etc/prompt-passage.yaml`. Mount a different file or set the `PROMPT_PASSAGE_CONFIG_PATH` environment variable to change the location.

