#!/usr/bin/env python3
"""
Start the proxy first, then run to hit the 'test' provider with streaming.
"""

import json
import os
import requests
import sys

ENDPOINT = "http://127.0.0.1:8095/provider/test/chat/completions"
MODEL = "o4-mini"
PROMPT = "I am going to Paris, what should I see?"
MAX_TOKENS = 1000
DEBUG = os.getenv("DEBUG") == "1"


def stream_chat() -> None:
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    payload = {
        "messages": [{"role": "user", "content": PROMPT}],
        "max_completion_tokens": MAX_TOKENS,
        "model": MODEL,
        "stream": True,
    }

    with requests.post(ENDPOINT, headers=headers, json=payload, stream=True) as resp:
        resp.raise_for_status()

        for raw_line in resp.iter_lines(decode_unicode=True):
            if not raw_line or not raw_line.startswith("data:"):
                continue  # skip keep-alives / non-data lines

            data = raw_line.removeprefix("data: ").strip()
            if data == "[DONE]":
                print()  # final newline
                break

            if DEBUG:
                print(f"\n[DEBUG raw] {data}", file=sys.stderr)

            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                print(f"\n[WARN] Could not parse: {data!r}", file=sys.stderr)
                continue

            # Extract a token if present and printable
            choices = chunk.get("choices") or []
            if not choices:
                continue

            first = choices[0]

            token = (
                first.get("delta", {}).get("content")  # OpenAI / Azure style
                or first.get("message", {}).get("content")  # some OSS gateways
                or first.get("content")  # older OSS variants
            )

            if token:
                print(token, end="", flush=True)


if __name__ == "__main__":
    try:
        stream_chat()
    except KeyboardInterrupt:
        print("\n[Interrupted]", file=sys.stderr)
