#!/usr/bin/env python3
"""
SkyGuard AI - Groq connectivity smoke test (zero dependencies).

Verifies that the GROQ_API_KEY in your .env can reach Groq and get a completion
from the configured model (openai/gpt-oss-20b). Uses only the Python standard
library, so you can run it before installing anything:

    python test_groq.py

It reads .env from the same folder as this file and never prints your full key.
Exit code 0 = success, 1 = failure (handy for CI / shell checks).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def load_env(path: Path) -> dict:
    """Minimal .env parser (KEY=VALUE lines). Real environment variables win."""
    values = {}
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip().strip('"').strip("'")
    for k in list(values):
        if os.environ.get(k):  # a real environment variable overrides the file
            values[k] = os.environ[k]
    return values


def main() -> int:
    env = load_env(Path(__file__).resolve().parent / ".env")
    api_key = env.get("GROQ_API_KEY", "")
    model = env.get("GROQ_MODEL", "openai/gpt-oss-20b")
    base_url = env.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
    try:
        temperature = float(env.get("GROQ_TEMPERATURE", "0.2"))
    except ValueError:
        temperature = 0.2
    try:
        max_tokens = int(env.get("GROQ_MAX_TOKENS", "1024"))
    except ValueError:
        max_tokens = 1024

    if not api_key or api_key.startswith("gsk_replace_me"):
        print("[FAIL] GROQ_API_KEY is missing or still the placeholder.")
        print("       Edit .env and paste your real key from https://console.groq.com/keys")
        return 1

    print(f"-> Model:    {model}")
    print(f"-> Endpoint: {base_url}/chat/completions")
    print(f"-> Key:      ...{api_key[-4:]} (length {len(api_key)})")
    print("-> Sending a one-line test prompt...\n")

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": "You are SkyGuard's assistant. Answer in one short sentence."},
            {"role": "user", "content": "In one sentence, what is an automatic weather station?"},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        print(f"[FAIL] HTTP {e.code} from Groq:\n{detail}")
        if e.code == 401:
            print("\n-> 401 = key rejected. Re-check it at https://console.groq.com/keys")
        elif e.code == 404:
            print(f"\n-> 404 may mean model id '{model}' is wrong. See https://console.groq.com/docs/models")
        return 1
    except urllib.error.URLError as e:
        print(f"[FAIL] Network error reaching Groq: {e.reason}")
        print("-> Check your internet connection / proxy, then retry.")
        return 1

    elapsed_ms = (time.time() - start) * 1000
    try:
        text = body["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        print(f"[FAIL] Unexpected response shape:\n{json.dumps(body, indent=2)[:800]}")
        return 1

    usage = body.get("usage", {})
    print("[OK] SUCCESS - Groq replied:\n")
    print(f"    {text}\n")
    print(
        f"-> Latency: {elapsed_ms:.0f} ms | tokens: "
        f"prompt {usage.get('prompt_tokens', '?')}, "
        f"completion {usage.get('completion_tokens', '?')}, "
        f"total {usage.get('total_tokens', '?')}"
    )
    print(f"-> Served model: {body.get('model', model)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
