import uvicorn
from .proxy_app import app


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8095)
