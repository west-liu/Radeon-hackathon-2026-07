#!/usr/bin/env python3
"""RadeonReviewer — multi-pass review agent."""

import json
import os
from typing import Any

import config
from prompts import DEEP_ANALYZE_SYSTEM, FAST_SCAN_SYSTEM, SUMMARY_PROMPT
from vllm_client import chat_completion


def _clean_json(raw: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(str(raw))
    except Exception:
        return {"issues": [], "raw": str(raw)}


def fast_scan(diff_text: str) -> dict[str, Any]:
    """Pass 1: lightweight syntax/style/naming scan."""
    print("[Agent] fast scan …")
    raw = chat_completion(
        system_prompt=FAST_SCAN_SYSTEM,
        user_prompt=f"Review the following git diff:\n\n```diff\n{diff_text}\n```",
        model=config.FAST_MODEL,
        max_tokens=2048,
    )
    return _clean_json(raw)


def deep_analyze(diff_text: str) -> dict[str, Any]:
    """Pass 2: security, logic, performance deep dive."""
    print("[Agent] deep analyze …")
    raw = chat_completion(
        system_prompt=DEEP_ANALYZE_SYSTEM,
        user_prompt=f"Review the following git diff:\n\n```diff\n{diff_text}\n```",
        model=config.DEEP_MODEL,
        max_tokens=4096,
    )
    return _clean_json(raw)


def synthesize_report(fast_result: dict[str, Any], deep_result: dict[str, Any]) -> str:
    """Pass 3: merge passes into a Markdown review report."""
    print("[Agent] synthesize …")
    fast_json = json.dumps(fast_result, ensure_ascii=False, indent=2)
    deep_json = json.dumps(deep_result, ensure_ascii=False, indent=2)

    prompt = SUMMARY_PROMPT.format(fast_json=fast_json, deep_json=deep_json)
    report = chat_completion(
        system_prompt="You are a senior engineering lead. Be concise.",
        user_prompt=prompt,
        json_mode=False,
        max_tokens=4096,
    )
    return str(report)


def review_pr(diff_text: str) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Run the full three-pass review pipeline."""
    fast = fast_scan(diff_text)
    deep = deep_analyze(diff_text)
    report = synthesize_report(fast, deep)
    return fast, deep, report
