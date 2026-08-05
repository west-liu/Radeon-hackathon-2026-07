#!/usr/bin/env python3
"""Parallel Universe Simulator — FastAPI server."""
import json
import sys
from typing import List, Optional
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel

import config
from parallel_universe import ParallelUniverseEngine

app = FastAPI(title="Parallel Universe Simulator", version="1.0.0")
engine = None

# ── Startup ─────────────────────────────────────────────────────────────────
@app.on_event("startup")
def _startup():
    global engine
    engine = ParallelUniverseEngine()

# ── Models ────────────────────────────────────────────────────────────────────
class LearnRequest(BaseModel):
    user_id: str
    notes: List[str]

class SimulateRequest(BaseModel):
    user_id: str
    decision: str
    n: Optional[int] = None
    depth: Optional[int] = None

class StressTestRequest(BaseModel):
    idea: str
    context: Optional[str] = ""

class CompareRequest(BaseModel):
    user_id: str
    universes: list  # type: ignore

# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    try:
        h = engine.client.health()
        return {"status": "ok" if h.get("ok") else "degraded", "llm": h}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}

@app.get("/")
def root():
    return {
        "name": "Parallel Universe Simulator",
        "description": "Local AI Agent that learns your personality and simulates alternative life paths",
        "endpoints": ["/health", "/learn", "/simulate", "/stress-test", "/compare", "/personality/{user_id}"]
    }

@app.post("/learn")
def learn(req: LearnRequest):
    profile = engine.learn(req.user_id, req.notes)
    return {
        "user_id": req.user_id,
        "profile": profile.__dict__,
        "memories_stored": len(req.notes),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/personality/{user_id}")
def get_personality(user_id: str):
    p = engine.personality.get(user_id)
    if not p:
        raise HTTPException(status_code=404, detail="Personality not found. Run /learn first.")
    return {"user_id": user_id, "profile": p.__dict__}

@app.post("/simulate")
def simulate(req: SimulateRequest):
    universes = engine.simulate(req.user_id, req.decision, req.n, req.depth)
    return {
        "user_id": req.user_id,
        "decision": req.decision,
        "universes": universes,
        "count": len(universes),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/stress-test")
def stress_test(req: StressTestRequest):
    result = engine.stress_test(req.idea, req.context)
    return {
        "idea": req.idea,
        "result": result,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/compare")
def compare(req: CompareRequest):
    verdict = engine.compare(req.user_id, req.universes)
    return {
        "user_id": req.user_id,
        "verdict": verdict,
        "timestamp": datetime.utcnow().isoformat()
    }

# ── CLI ─────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--health":
        h = ParallelUniverseEngine().client.health()
        print("LLM health:", "OK" if h.get("ok") else "FAIL", h)
        return
    uvicorn.run("main:app", host=config.API_HOST, port=config.API_PORT, reload=False)

if __name__ == "__main__":
    main()
