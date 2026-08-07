#!/usr/bin/env python3
"""Send one SupplyChain-TLM prompt to a persistent llama.cpp server."""

from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main() -> int:
    prompt = sys.stdin.read()
    base_url = os.environ.get("LLAMA_SERVER_URL", "http://127.0.0.1:8081").rstrip("/")
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": int(os.environ.get("QWEN_MAX_NEW", "128")),
        "stream": False,
    }
    request = Request(
        f"{base_url}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=float(os.environ.get("LLAMA_SERVER_TIMEOUT", "180"))) as response:
            result = json.load(response)
    except (HTTPError, URLError, TimeoutError) as error:
        print(f"llama-server request failed: {error}", file=sys.stderr)
        return 1
    try:
        message = result["choices"][0]["message"]
        content = message.get("content") or message.get("reasoning_content") or ""
    except (KeyError, IndexError, TypeError) as error:
        print(f"llama-server returned an invalid response: {error}", file=sys.stderr)
        return 1
    if not str(content).strip():
        print("llama-server returned no usable answer", file=sys.stderr)
        return 1
    print(str(content).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
