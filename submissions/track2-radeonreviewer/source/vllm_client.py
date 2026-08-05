#!/usr/bin/env python3
"""RadeonReviewer — thin OpenAI-compatible client talking to vLLM or AMD Token Factory."""

import json
import os
from typing import Any

import httpx
from config import API_KEY, LLM_BASE_URL, MAX_TOKENS, MODEL_ID, TEMPERATURE

TIMEOUT = httpx.Timeout(300.0, connect=30.0)


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=LLM_BASE_URL,
        headers={"Authorization": f"Bearer {API_KEY}"} if API_KEY else {},
        timeout=TIMEOUT,
    )


def chat_completion(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    json_mode: bool = True,
) -> dict[str, Any] | str:
    """Call the LLM endpoint. Returns parsed JSON when json_mode=True."""
    payload = {
        "model": model or MODEL_ID,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature if temperature is not None else TEMPERATURE,
        "max_tokens": max_tokens if max_tokens is not None else MAX_TOKENS,
    }

    with _client() as client:
        resp = client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()

    text = data["choices"][0]["message"]["content"]

    if not json_mode:
        return text

    # vLLM may wrap JSON in markdown fences; strip them.
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: return raw text so the caller can log / retry.
        return {"raw": text}
