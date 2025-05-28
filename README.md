# local-llm-proxy

Proxy local LLM calls to Azure


## Example config

```yaml
models:
  gpt-4o-mini:
    endpoint: "https://api.openai.com/v1/chat/completions"
    envKey: "OPENAI_API_KEY"
```

## Dev environment setup

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

make install
```