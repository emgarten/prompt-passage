#!/usr/bin/env python3
"""Simple functional test hitting the 'test' provider once."""

import json
import os
import sys
import requests

ENDPOINT = "http://127.0.0.1:8095/provider/test/chat/completions"
MODEL = "o4-mini"
PROMPT = "I am going to Paris, what should I see?"
MAX_TOKENS = 2048
DEBUG = os.getenv("DEBUG") == "1"


def chat_once() -> None:
    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "messages": [{"role": "user", "content": PROMPT}],
        "max_completion_tokens": MAX_TOKENS,
        "model": MODEL,
    }

    resp = requests.post(ENDPOINT, headers=headers, json=payload)
    resp.raise_for_status()

    data = resp.json()
    if DEBUG:
        print(json.dumps(data, indent=2))
        return

    try:
        print(data["choices"][0]["message"]["content"])
    except Exception:
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    try:
        chat_once()
    except KeyboardInterrupt:
        print("\n[Interrupted]", file=sys.stderr)
