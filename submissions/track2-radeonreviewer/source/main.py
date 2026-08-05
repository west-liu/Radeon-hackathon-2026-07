#!/usr/bin/env python3
"""RadeonReviewer — FastAPI server + GitHub webhook + CLI entry."""

import hashlib
import hmac
import json
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

import config
from agent import review_pr
from tools import fetch_pr_diff, parse_diff_files, truncate_diff

GITHUB_WEBHOOK_SECRET = config.GITHUB_WEBHOOK_SECRET
REVIEW_DB = config.REVIEW_DB_PATH


def _init_db() -> None:
    os.makedirs(os.path.dirname(REVIEW_DB) or ".", exist_ok=True)
    with sqlite3.connect(REVIEW_DB) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT,
                repo TEXT,
                pr_number INTEGER,
                created_at TEXT,
                fast_issues INTEGER,
                deep_issues INTEGER,
                report TEXT
            )
            """
        )


def _store_review(owner: str, repo: str, pr_number: int, fast: dict, deep: dict, report: str) -> None:
    with sqlite3.connect(REVIEW_DB) as conn:
        conn.execute(
            "INSERT INTO reviews (owner, repo, pr_number, created_at, fast_issues, deep_issues, report) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                owner,
                repo,
                pr_number,
                datetime.utcnow().isoformat(),
                len(fast.get("issues", [])),
                len(deep.get("issues", [])),
                report,
            ),
        )


# ---------------------------------------------------------------------------
# FastAPI lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_db()
    yield


app = FastAPI(title="RadeonReviewer", version="1.0.0", lifespan=lifespan)


class ReviewRequest(BaseModel):
    owner: str
    repo: str
    pr_number: int


class DiffReviewRequest(BaseModel):
    diff: str


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "agent": "RadeonReviewer", "gpu": "AMD Radeon"}


@app.post("/review")
async def review_endpoint(req: ReviewRequest) -> dict[str, Any]:
    """HTTP API: review a GitHub PR by owner/repo/number."""
    diff = fetch_pr_diff(req.owner, req.repo, req.pr_number)
    diff = truncate_diff(diff, config.PR_MAX_TOTAL_LINES)
    fast, deep, report = review_pr(diff)
    _store_review(req.owner, req.repo, req.pr_number, fast, deep, report)
    return {"owner": req.owner, "repo": req.repo, "pr_number": req.pr_number, "report": report}


@app.post("/review/diff")
async def review_diff_endpoint(req: DiffReviewRequest) -> dict[str, Any]:
    """HTTP API: review raw diff text directly."""
    fast, deep, report = review_pr(req.diff)
    return {"report": report}


@app.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
) -> JSONResponse:
    """GitHub webhook entry: triggered on PR opened/synchronize."""
    payload = await request.body()
    if GITHUB_WEBHOOK_SECRET and x_hub_signature_256:
        sig = hmac.new(GITHUB_WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(f"sha256={sig}", x_hub_signature_256):
            raise HTTPException(status_code=403, detail="Invalid signature")

    event = json.loads(payload)
    if x_github_event not in ("pull_request", "pull_request_opened"):
        return JSONResponse({"ignored": True, "event": x_github_event})

    if event.get("action") not in ("opened", "synchronize", "reopened"):
        return JSONResponse({"ignored": True, "action": event.get("action")})

    owner = event["repository"]["owner"]["login"]
    repo = event["repository"]["name"]
    pr_number = event["pull_request"]["number"]

    diff = fetch_pr_diff(owner, repo, pr_number)
    diff = truncate_diff(diff, config.PR_MAX_TOTAL_LINES)
    fast, deep, report = review_pr(diff)
    _store_review(owner, repo, pr_number, fast, deep, report)

    # (Optional) post back to GitHub PR comment via API — left as exercise for completeness.
    return JSONResponse({"owner": owner, "repo": repo, "pr_number": pr_number, "status": "reviewed"})


@app.get("/reviews")
async def list_reviews(owner: str | None = None, repo: str | None = None) -> list[dict[str, Any]]:
    with sqlite3.connect(REVIEW_DB) as conn:
        conn.row_factory = sqlite3.Row
        sql = "SELECT * FROM reviews WHERE 1=1"
        params: list[Any] = []
        if owner:
            sql += " AND owner = ?"
            params.append(owner)
        if repo:
            sql += " AND repo = ?"
            params.append(repo)
        sql += " ORDER BY created_at DESC"
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------
def cli_review() -> None:
    import sys
    if len(sys.argv) < 4:
        print("Usage: python main.py <owner> <repo> <pr_number>")
        sys.exit(1)
    owner, repo, pr_number = sys.argv[1], sys.argv[2], int(sys.argv[3])
    diff = fetch_pr_diff(owner, repo, pr_number)
    files = parse_diff_files(diff)
    print(f"[CLI] PR #{pr_number} — {len(files)} file(s) changed")
    diff = truncate_diff(diff, config.PR_MAX_TOTAL_LINES)
    fast, deep, report = review_pr(diff)
    _store_review(owner, repo, pr_number, fast, deep, report)
    print("\n" + "=" * 60)
    print(report)
    print("=" * 60)


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        cli_review()
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
