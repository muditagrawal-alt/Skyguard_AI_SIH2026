"""
SkyGuard AI - Groq LLM client (OpenAI-compatible).

A thin wrapper over Groq's chat-completions API, used to turn SkyGuard's
structured detector output into plain-language narration and to power any
assistant features. Configuration comes from environment variables, with a
fallback to the repo-root .env file so no python-dotenv dependency is required:

    GROQ_API_KEY      (required)
    GROQ_MODEL        default: openai/gpt-oss-20b
    GROQ_BASE_URL     default: https://api.groq.com/openai/v1
    GROQ_TEMPERATURE  default: 0.2
    GROQ_MAX_TOKENS   default: 1024

Networking uses `requests` (already a project dependency). The API key is a
secret: it lives only in .env (git-ignored) and is never logged or returned to
clients.
"""
from __future__ import annotations

import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# backend/app/core/llm.py -> parents[3] is the repo root, where .env lives.
_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
_PLACEHOLDER_PREFIX = "gsk_replace_me"


@lru_cache(maxsize=1)
def _env_file_values() -> Dict[str, str]:
    """Parse the repo-root .env once (KEY=VALUE lines). Cached for the process."""
    values: Dict[str, str] = {}
    if _ENV_PATH.exists():
        for raw in _ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def _get(name: str, default: str = "") -> str:
    """Environment variable, falling back to the .env file, then the default."""
    val = os.environ.get(name)
    if val is not None:
        return val
    return _env_file_values().get(name, default)


def llm_config() -> Dict[str, Any]:
    """Resolved configuration. `configured` is False when no real key is present."""
    api_key = _get("GROQ_API_KEY")
    try:
        temperature = float(_get("GROQ_TEMPERATURE", "0.2"))
    except ValueError:
        temperature = 0.2
    try:
        max_tokens = int(_get("GROQ_MAX_TOKENS", "1024"))
    except ValueError:
        max_tokens = 1024
    return {
        "api_key": api_key,
        "model": _get("GROQ_MODEL", "openai/gpt-oss-20b"),
        "base_url": _get("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/"),
        "temperature": temperature,
        "max_tokens": max_tokens,
        "configured": bool(api_key) and not api_key.startswith(_PLACEHOLDER_PREFIX),
    }


class LLMError(RuntimeError):
    """Raised when the LLM is unconfigured or the Groq call fails."""


def chat(
    messages: List[Dict[str, str]],
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """
    Send chat messages to Groq and return {text, model, latency_ms, usage}.
    Raises LLMError if the client is unconfigured or the request fails.
    """
    cfg = llm_config()
    if not cfg["configured"]:
        raise LLMError(
            "Groq is not configured: set a real GROQ_API_KEY in .env "
            "(it is currently missing or still the placeholder)."
        )

    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": cfg["temperature"] if temperature is None else temperature,
        "max_tokens": cfg["max_tokens"] if max_tokens is None else max_tokens,
    }
    start = time.time()
    try:
        resp = requests.post(
            f"{cfg['base_url']}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {cfg['api_key']}"},
            timeout=timeout,
        )
    except requests.RequestException as e:
        raise LLMError(f"Network error reaching Groq: {e}") from e

    if resp.status_code != 200:
        # Surface Groq's error body (it never contains the key) to aid debugging.
        raise LLMError(f"Groq returned HTTP {resp.status_code}: {resp.text[:500]}")

    body = resp.json()
    try:
        text = body["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        raise LLMError(f"Unexpected Groq response shape: {str(body)[:500]}") from e

    return {
        "text": text,
        "model": body.get("model", cfg["model"]),
        "latency_ms": round((time.time() - start) * 1000, 1),
        "usage": body.get("usage", {}),
    }


def health() -> Dict[str, Any]:
    """
    Lightweight round-trip used by GET /api/llm/health. Never raises: returns
    {ok, ...} on success or {ok: False, error} so the endpoint can report status
    cleanly. Never includes the API key.
    """
    cfg = llm_config()
    if not cfg["configured"]:
        return {
            "ok": False,
            "configured": False,
            "model": cfg["model"],
            "error": "GROQ_API_KEY missing or still the placeholder in .env.",
        }
    try:
        res = chat([{"role": "user", "content": "Reply with exactly: OK"}], max_tokens=5)
        return {
            "ok": True,
            "configured": True,
            "model": res["model"],
            "latency_ms": res["latency_ms"],
            "sample": res["text"],
            "usage": res["usage"],
        }
    except LLMError as e:
        return {"ok": False, "configured": True, "model": cfg["model"], "error": str(e)}
