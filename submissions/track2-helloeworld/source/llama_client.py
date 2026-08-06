"""
Hello E World — llama.cpp Client
Calls local llama.cpp server running Qwen2.5-14B-Instruct on W7900.
"""

import os
import json
import httpx
from typing import Optional, AsyncIterator

LLAMA_BASE = os.getenv("LLAMA_BASE", "http://127.0.0.1:8000/v1")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "Qwen2.5-14B-Instruct")
LLAMA_TIMEOUT = int(os.getenv("LLAMA_TIMEOUT", "120"))


async def chat(
    prompt: str,
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    stream: bool = False,
) -> dict:
    """Call llama.cpp server (OpenAI-compatible API)."""
    headers = {"Content-Type": "application/json"}
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": LLAMA_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=LLAMA_TIMEOUT) as client:
        resp = await client.post(
            f"{LLAMA_BASE}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


async def chat_stream(
    prompt: str,
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> AsyncIterator[str]:
    """Stream tokens from llama.cpp server."""
    headers = {"Content-Type": "application/json"}
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": LLAMA_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=LLAMA_TIMEOUT) as client:
        async with client.stream(
            "POST",
            f"{LLAMA_BASE}/chat/completions",
            headers=headers,
            json=payload,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue


def extract_text(response: dict) -> str:
    """Extract text from OpenAI-compatible response."""
    return response["choices"][0]["message"]["content"]


def extract_json(text: str) -> dict:
    """Extract JSON from model output, handling markdown fences."""
    import re
    cleaned = text.strip()
    # Remove markdown fences
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON block
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        return {"error": "parse_failed", "raw": text[:500]}
