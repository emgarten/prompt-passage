import argparse
import logging
import os
from typing import Any
import uvicorn

from .proxy_app import app
from .config import load_config, default_config_path, ServiceCfg


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8095)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    config_path = default_config_path()
    if args.config:
        # Use the provided config path if specified
        config_path = args.config

    if not os.path.exists(config_path):
        logging.error(f"Configuration file '{config_path}' does not exist.")
        exit(1)
    else:
        logging.info(f"Using configuration file: {config_path}")

    cfg = load_config(config_path)
    port = cfg.service.port if cfg and cfg.service else ServiceCfg().port
    if args.port:
        # Override port from command line argument if provided
        port = args.port

    certfile = os.getenv("PROMPT_PASSAGE_CERTFILE")
    keyfile = os.getenv("PROMPT_PASSAGE_KEYFILE")
    ca_certs = os.getenv("PROMPT_PASSAGE_CA_CERTS")

    uvicorn_kwargs: dict[str, Any] = {
        "host": args.host,
        "port": port,
        "workers": args.workers,
    }
    if certfile:
        uvicorn_kwargs["ssl_certfile"] = certfile
    if keyfile:
        uvicorn_kwargs["ssl_keyfile"] = keyfile
    if ca_certs:
        uvicorn_kwargs["ssl_ca_certs"] = ca_certs

    uvicorn.run(app, **uvicorn_kwargs)


if __name__ == "__main__":
    main()
