from local_llm_proxy.config import AuthConfig, ProviderCfg, RootConfig, build_model_map
from local_llm_proxy.token_providers import ApiKeyProvider, AzCliTokenProvider


def test_build_model_map_creates_providers() -> None:
    config = RootConfig(
        providers={
            "env": ProviderCfg(endpoint="https://example.com", model="m1", auth=AuthConfig(type="apikey", key="abc")),
            "cli": ProviderCfg(endpoint="https://example.com", model="m2", auth=AuthConfig(type="azcli")),
        }
    )

    model_map = build_model_map(config)
    assert isinstance(model_map["env"].token_provider, ApiKeyProvider)
    assert isinstance(model_map["cli"].token_provider, AzCliTokenProvider)
