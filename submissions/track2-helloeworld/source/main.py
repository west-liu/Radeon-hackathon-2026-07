"""
Hello E World — FastAPI Server
Onboarding → Personality Extraction → What-If Simulation
All inference on local AMD Radeon GPU via llama.cpp.
"""

import os
import json
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel

from agent import (
    get_next_question, extract_personality,
    simulate_whatif, simulate_whatif_stream,
    stress_test_idea,
)
from tools import PersonalityProfile, WhatIfReport

LLAMA_BASE = os.getenv("LLAMA_BASE", "http://127.0.0.1:8000/v1")

# ─── State (per-session, in-memory for MVP) ──────────────────────
qa_history: list[dict] = []
profile: PersonalityProfile | None = None

# ─── App ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 60)
    print("🔮 Hello E World — Parallel Universe Simulator")
    print(f"   llama.cpp: {LLAMA_BASE}")
    print("   GPU:  AMD Radeon Pro W7900 (48GB)")
    print("=" * 60 + "\n")
    yield

app = FastAPI(title="Hello E World", version="0.1.0", lifespan=lifespan)


# ─── Models ──────────────────────────────────────────────────────

class AnswerRequest(BaseModel):
    answer: str

class ScenarioRequest(BaseModel):
    scenario: str

class ResetRequest(BaseModel):
    pass


# ─── Frontend ────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    frontend = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend.exists():
        return frontend.read_text(encoding="utf-8")
    return HTMLResponse("<h1>Hello E World</h1><p>Frontend not found.</p>")


# ─── Health ──────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "llama": LLAMA_BASE,
        "gpu": "AMD Radeon Pro W7900 (48GB)",
        "qa_count": len(qa_history),
        "has_profile": profile is not None,
    }


# ─── Onboarding ──────────────────────────────────────────────────

@app.get("/onboard/next-question")
async def next_question():
    """Get the next interview question based on current history."""
    try:
        q = await get_next_question(qa_history)
        return {"question": q, "question_number": len(qa_history) + 1}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"llama.cpp error: {str(e)}")


@app.post("/onboard/answer")
async def submit_answer(req: AnswerRequest):
    """Submit answer to current question."""
    # Get current question first
    try:
        q = await get_next_question(qa_history)
    except Exception:
        q = "Tell me more about that."

    qa_history.append({"question": q, "answer": req.answer})
    return {
        "total_answered": len(qa_history),
        "qa_history": qa_history,
    }


@app.get("/onboard/history")
async def get_history():
    return {"qa_history": qa_history, "count": len(qa_history)}


# ─── Personality ─────────────────────────────────────────────────

@app.post("/personality/extract")
async def extract():
    """Extract personality profile from onboarding Q&A."""
    global profile
    if len(qa_history) < 3:
        raise HTTPException(status_code=400, detail="Need at least 3 Q&A pairs")

    try:
        profile = await extract_personality(qa_history)
        return {
            "profile": profile.to_dict(),
            "qa_count": len(qa_history),
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"llama.cpp error: {str(e)}")


@app.get("/personality")
async def get_profile():
    if profile is None:
        raise HTTPException(status_code=404, detail="No profile extracted yet")
    return {"profile": profile.to_dict()}


# ─── What-If Simulation ──────────────────────────────────────────

@app.post("/simulate")
async def simulate(req: ScenarioRequest):
    """Run what-if simulation. Returns full report."""
    global profile
    if profile is None:
        raise HTTPException(status_code=400, detail="Extract personality first")

    try:
        report = await simulate_whatif(profile, req.scenario)
        return {
            "report": report.to_dict(),
            "markdown": report.format_markdown(),
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"llama.cpp error: {str(e)}")


# ─── Stress Test ──────────────────────────────────────────────────

class StressTestRequest(BaseModel):
    idea: str
    context: str = ""

@app.post("/stress-test")
async def stress_test(req: StressTestRequest):
    """Run a 4-role stress test on an idea (VC/Customer/Competitor/Regulator)."""
    try:
        result = await stress_test_idea(req.idea, req.context)
        return {"idea": req.idea, "result": result}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"llama.cpp error: {str(e)}")


# ─── Reset ───────────────────────────────────────────────────────

@app.post("/reset")
async def reset():
    global qa_history, profile
    qa_history = []
    profile = None
    return {"status": "reset"}


# ─── Quick Demo Mode ─────────────────────────────────────────────

@app.post("/demo/quick-start")
async def demo_quick_start():
    """Preload demo Q&A so you can jump straight to simulation."""
    global qa_history
    qa_history = [
        {"question": "What's a decision that changed everything?", "answer": "Leaving my corporate job at 28 to start a company. Everyone said it was too early, I didn't have enough savings, but I felt like if I didn't do it then I never would."},
        {"question": "How did you make that decision?", "answer": "I made a spreadsheet at first — salary projections, burn rate, worst case. But honestly the real decision was emotional: I looked at my boss and thought 'I don't want his life.' That was it."},
        {"question": "What are you most afraid of right now?", "answer": "That I'm building something nobody actually needs. I can handle failure if I know I tried the right thing. But the idea that I might be deluding myself — that's the one that keeps me up."},
        {"question": "Who shaped you most?", "answer": "My dad, who worked the same job for 35 years and never complained. He gave me stability. And my first co-founder, who taught me that being right is less important than being effective."},
        {"question": "What are you really good at?", "answer": "I can see patterns in chaos. When a project is falling apart or a team is in conflict, I can usually trace it back to one or two root causes that nobody else sees. Also, I'm good at making people feel heard."},
        {"question": "What's your worst trait?", "answer": "I hold grudges. Not openly — I'm very good at pretending I've moved on — but internally I remember everything. Also, I procrastinate on hard conversations until they become crises."},
    ]
    return {"status": "demo_loaded", "qa_count": len(qa_history)}
