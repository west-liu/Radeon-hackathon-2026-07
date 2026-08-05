#!/usr/bin/env python3
"""RadeonReviewer — tool definitions (PR diff parsing)."""

import base64
import os
import re
from pathlib import Path
from typing import Any

import httpx

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


def _github_headers() -> dict[str, str]:
    h = {"Accept": "application/vnd.github.v3+json", "User-Agent": "RadeonReviewer"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"token {GITHUB_TOKEN}"
    return h


def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch the unified diff for a GitHub PR."""
    url = f"https://github.com/{owner}/{repo}/pull/{pr_number}.diff"
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, headers=_github_headers())
        resp.raise_for_status()
        return resp.text


def fetch_repo_file(owner: str, repo: str, ref: str, path: str) -> str:
    """Fetch a single file from a GitHub repo at a given ref."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, headers=_github_headers())
        resp.raise_for_status()
        data = resp.json()
        content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return content


def parse_diff_files(diff_text: str) -> list[dict[str, Any]]:
    """Split a unified diff into per-file hunks."""
    files = []
    current: dict[str, Any] | None = None
    for line in diff_text.splitlines(keepends=True):
        if line.startswith("diff --git"):
            if current:
                files.append(current)
            # Extract filename from "diff --git a/... b/..."
            m = re.search(r"diff --git a/(.*?) b/", line)
            fname = m.group(1) if m else "unknown"
            current = {"filename": fname, "diff": line}
        elif current is not None:
            current["diff"] += line
    if current:
        files.append(current)
    return files


def truncate_diff(diff_text: str, max_lines: int = 3000) -> str:
    """Truncate diff to stay within LLM context budget."""
    lines = diff_text.splitlines()
    if len(lines) <= max_lines:
        return diff_text
    # Keep header lines and first N/2 + last N/2 for large diffs.
    half = max_lines // 2
    truncated = lines[:half] + ["\n\n... [diff truncated: too large] ...\n\n"] + lines[-half:]
    return "\n".join(truncated)
