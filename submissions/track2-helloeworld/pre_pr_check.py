#!/usr/bin/env python3
"""
Pre-PR Checklist for Hello E World — Track 2 Submission
Run this before creating the PR to AMD-DEV-CONTEST.
Deadline: 2026-08-06 23:59 Beijing Time
"""

import os
import sys
import re
import subprocess
from pathlib import Path
from datetime import datetime

# ─── Paths ─────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent.parent  # Radeon-hackathon-2026-07
SUBMISSION = REPO_ROOT / "submissions" / "track2-helloeworld"
REQUIRED_FILES = {
    "README.md": "Project overview, install, run instructions",
    "PROJECT_SPEC.md": "Detailed spec for judges",
    "source/main.py": "FastAPI server entry",
    "source/agent.py": "Core agent logic",
    "source/llama_client.py": "llama.cpp client (was vllm_client.py)",
    "source/tools.py": "Data structures",
    "source/__init__.py": "Package init",
    "frontend/index.html": "Web UI",
    "presentation/slides.html": "Pitch deck (10 slides)",
    "start.sh": "One-command startup script",
    "docs/VISION.md": "Project vision",
    "docs/PRODUCT.md": "Product requirements",
}

BLOCKLIST = [
    ("vLLM|vllm|VLLM", "vLLM reference (should be llama.cpp)"),
    ("Parallex", "Old project name (should be Hello E World)"),
]

# ─── Colors ────────────────────────────────────────────────────────
class C:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"

def ok(msg): print(f"{C.GREEN}✓{C.RESET} {msg}")
def fail(msg): print(f"{C.RED}✗{C.RESET} {msg}")
def warn(msg): print(f"{C.YELLOW}⚠{C.RESET} {msg}")
def info(msg): print(f"{C.BLUE}ℹ{C.RESET} {msg}")

# ─── Checks ────────────────────────────────────────────────────────
errors = 0
warnings = 0

def check_files():
    global errors
    info("\n=== 1. Required Files ===")
    for rel, desc in REQUIRED_FILES.items():
        path = SUBMISSION / rel
        if path.exists():
            size = path.stat().st_size
            ok(f"{rel} ({size:,} bytes) — {desc}")
        else:
            fail(f"{rel} MISSING — {desc}")
            errors += 1

def check_blocklist():
    global errors, warnings
    info("\n=== 2. Blocked Terms (vLLM, Parallex, etc.) ===")
    found_any = False
    for pattern, reason in BLOCKLIST:
        regex = re.compile(pattern, re.IGNORECASE)
        for root, dirs, files in os.walk(SUBMISSION):
            # Skip binaries and git
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__"}]
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext in {".pyc", ".pyo", ".png", ".jpg", ".jpeg", ".gif", ".ico"}:
                    continue
                fpath = Path(root) / fname
                try:
                    text = fpath.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    continue
                matches = regex.findall(text)
                if matches:
                    found_any = True
                    count = len(matches)
                    fail(f"{fpath.relative_to(SUBMISSION)}: {count}x '{pattern}' — {reason}")
                    errors += count
    if not found_any:
        ok("No blocked terms found in submission directory.")

def check_chinese():
    global warnings
    info("\n=== 3. Chinese Character Check (materials must be EN) ===")
    chinese_re = re.compile(r'[\u4e00-\u9fff]')
    found = False
    for root, dirs, files in os.walk(SUBMISSION):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__"}]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in {".md", ".html", ".txt", ".py", ".sh", ".js", ".css"}:
                continue
            fpath = Path(root) / fname
            try:
                text = fpath.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            chars = chinese_re.findall(text)
            if chars:
                found = True
                unique = set(chars)
                count = len(chars)
                warn(f"{fpath.relative_to(SUBMISSION)}: {count} Chinese chars ({len(unique)} unique)")
                warnings += 1
    if not found:
        ok("No Chinese characters in text files.")

def check_git_status():
    info("\n=== 4. Git Status ===")
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--short"],
        capture_output=True, text=True,
    )
    if result.stdout.strip():
        lines = result.stdout.strip().split("\n")
        warn(f"{len(lines)} uncommitted change(s):")
        for line in lines:
            print(f"    {line}")
    else:
        ok("Working tree clean — ready to PR.")

def check_git_remote():
    info("\n=== 5. Git Remotes ===")
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "remote", "-v"],
        capture_output=True, text=True,
    )
    print(result.stdout)
    if "AMD-DEV-CONTEST" in result.stdout:
        ok("Upstream remote (AMD-DEV-CONTEST) found.")
    else:
        warn("Upstream remote not found. PR will be manual.")

def generate_pr_body():
    info("\n=== 6. PR Description (copy-paste ready) ===")
    body = """## Track 2 Submission: Hello E World

**Team:** silent core
**Track:** 2 — Private AI Agent Development
**Project:** Hello E World — IP World Simulation Engine

### What It Does
Hello E World transforms any novel into a living, playable universe. Upload a book, pick a character, and step inside the story. AI generates canon-consistent scenes in real-time; your choices ripple through the narrative via a dual-agent architecture (Foreground Scene Director + Background Fate Worker).

### Why It Fits Track 2
- ✅ **Local GPU inference** — 100% on AMD Radeon Pro W7900 via llama.cpp + ROCm. Zero API calls.
- ✅ **Agent properties** — Dual-agent system with real-time planning, memory (Redis + PostgreSQL), tool calling, and state persistence.
- ✅ **Privacy** — All novels, chats, and world states stay on the local machine.
- ✅ **Reproducible** — One-command startup via `start.sh` or Docker.

### Tech Stack
- **Inference:** llama.cpp (OpenAI-compatible API) + Qwen2.5-14B-Instruct on W7900
- **Backend:** FastAPI, dual-agent loop, Redis Streams event bus, optimistic locking
- **Storage:** PostgreSQL (persistent), Redis (session state), SQLite (ice library RAG)
- **Frontend:** React + Tailwind (SSE streaming for real-time text)
- **GPU:** AMD Radeon Pro W7900 48GB, ROCm 7.2.1

### Files Added
- `submissions/track2-helloeworld/` — Complete source code, docs, frontend, pitch deck

### Checklist
- [x] Source code complete
- [x] README with install/run instructions
- [x] Project specification document
- [x] Pitch deck (`presentation/slides.html`, 10 slides)
- [x] All inference runs locally on AMD GPU
- [x] No proprietary API dependency
- [x] Code is open-source and reproducible

---
*All materials prepared for AMD AI DevMaster Radeon GPU Hackathon 2026.*
"""
    print(body)
    return body

def print_deadline():
    now = datetime.now()
    deadline = datetime(2026, 8, 6, 23, 59)
    delta = deadline - now
    hours = int(delta.total_seconds() // 3600)
    minutes = int((delta.total_seconds() % 3600) // 60)
    info(f"\n=== Deadline ===")
    print(f"   Now:     {now.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Deadline: 2026-08-06 23:59 Beijing Time")
    if delta.total_seconds() > 0:
        print(f"   Remaining: {hours}h {minutes}m")
    else:
        fail("DEADLINE PASSED")

# ─── Main ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"{'='*60}")
    print("  Hello E World — Pre-PR Submission Checker")
    print(f"{'='*60}")

    check_files()
    check_blocklist()
    check_chinese()
    check_git_status()
    check_git_remote()
    pr_body = generate_pr_body()
    print_deadline()

    # Save PR body to file
    pr_file = SUBMISSION / "PR_BODY.md"
    pr_file.write_text(pr_body, encoding="utf-8")
    info(f"\nPR description saved to: {pr_file}")

    info("\n=== Summary ===")
    if errors == 0 and warnings == 0:
        ok("All checks passed! Ready to create PR.")
        print(f"\n   Manual PR link:")
        print(f"   https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/compare/main...west-liu:main")
    elif errors == 0:
        warn(f"{warnings} warning(s) — review before PR, but not blocking.")
    else:
        fail(f"{errors} error(s), {warnings} warning(s) — FIX BEFORE PR.")
        sys.exit(1)
