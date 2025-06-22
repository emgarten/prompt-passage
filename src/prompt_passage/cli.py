import uvicorn

from .proxy_app import app
from .config import load_config, default_config_path, ServiceCfg


def main() -> None:
    config_path = default_config_path()
    try:
        cfg = load_config(config_path)
    except Exception:
        cfg = None

    port = cfg.service.port if cfg and cfg.service else ServiceCfg().port
    uvicorn.run(app, host="0.0.0.0", port=port)
