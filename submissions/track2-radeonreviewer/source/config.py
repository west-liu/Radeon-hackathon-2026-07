#!/usr/bin/env python3
"""RadeonReviewer — configuration constants."""

import os

# ---------------------------------------------------------------------------
# vLLM endpoints (set to AMD API for demo; swap to localhost when self-hosting)
# ---------------------------------------------------------------------------
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:8000/v1")
MODEL_ID = os.getenv("MODEL_ID", "Qwen/Qwen2.5-14B-Instruct")
API_KEY = os.getenv("API_KEY", "dummy_key")

# Two-model mode (optional — same API, different system prompts)
FAST_MODEL = os.getenv("FAST_MODEL", MODEL_ID)
DEEP_MODEL = os.getenv("DEEP_MODEL", MODEL_ID)

# ---------------------------------------------------------------------------
# Runtime parameters
# ---------------------------------------------------------------------------
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
LOG_DIR = os.getenv("LOG_DIR", "./logs")
REVIEW_DB_PATH = os.getenv("REVIEW_DB_PATH", "./reviews.sqlite")

# ---------------------------------------------------------------------------
# GitHub webhook / repo scanning
# ---------------------------------------------------------------------------
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
REPO_SCAN_DEPTH = int(os.getenv("REPO_SCAN_DEPTH", "3"))
PR_MAX_FILES = int(os.getenv("PR_MAX_FILES", "50"))
PR_MAX_LINES_PER_FILE = int(os.getenv("PR_MAX_LINES_PER_FILE", "300"))
PR_MAX_TOTAL_LINES = int(os.getenv("PR_MAX_TOTAL_LINES", "3000"))

# ---------------------------------------------------------------------------
# Streaming & back-pressure
# ---------------------------------------------------------------------------
SSE_RETRY_MS = 5000

# ---------------------------------------------------------------------------
# Prompt routing
# ---------------------------------------------------------------------------
FAST_SYSTEM_PROMPT = "fast_scan"
DEEP_SYSTEM_PROMPT = "deep_analyze"
