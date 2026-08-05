"""vLLM OpenAI-compatible API client."""
import json
import httpx
from typing import Dict, Any, Optional
import config

class VLLMClient:
    def __init__(self, base_url: str = config.VLLM_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=120.0)

    def chat(self, system: str, user: str, json_mode: bool = False) -> str:
        payload = {
            "model": config.MODEL_ID,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": config.TEMPERATURE,
            "max_tokens": config.MAX_TOKENS
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        resp = self.client.post(f"{self.base_url}/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def health(self) -> Dict[str, Any]:
        try:
            r = self.client.get(f"{self.base_url}/models", timeout=5)
            return {"ok": r.status_code == 200, "status": r.status_code}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def close(self):
        self.client.close()
