"""Ollama 로컬 서버 클라이언트."""

import os

import httpx

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("TEXT2SQL_MODEL", "qwen2.5-coder:3b")


def chat(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    timeout_s: float = 120.0,
    temperature: float = 0.0,
    seed: int = 42,
) -> str:
    options = {"temperature": temperature}
    if temperature > 0:
        options["seed"] = seed  # 샘플링해도 결과를 재현할 수 있게
    resp = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False,
            "options": options,
        },
        timeout=timeout_s,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]
