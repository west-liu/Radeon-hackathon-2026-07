"""
Parallex — Core Agent
Onboarding Interview → Personality Extraction → What-If Simulation
"""

import json
import time
from typing import AsyncIterator
from datetime import datetime

from .vllm_client import chat, chat_stream, extract_text, extract_json
from .tools import (
    PersonalityProfile, ParallelPath, WhatIfReport,
    ONBOARDING_POOL,
)

# ─── System prompts ─────────────────────────────────────────────

INTERVIEWER_SYSTEM = """You are a thoughtful, perceptive interviewer. Your job: learn who this person really is.

Rules:
- Ask ONE question at a time. Never ask multiple.
- Your next question should follow naturally from their answer. If they revealed something deep, go deeper. If they were surface-level, gently push.
- Vary the question type: some about facts, some about feelings, some about patterns.
- Never judge. If they say something vulnerable, acknowledge it before moving on.
- After 7-10 exchanges, you'll have enough. But don't count mechanically — stop when you genuinely understand them.
- Output ONLY your next question, nothing else. No "Great answer!" no "Thanks for sharing." Just the question.

The onboarding pool themes: education/career background, decision-making style, core values, risk tolerance, key relationships, self-perception, regrets and future.

Start with something warm but not generic. Don't ask "how are you" — ask something that makes them think."""

PERSONA_EXTRACTOR_SYSTEM = """You are a personality analyst. Given a Q&A transcript, extract a structured personality profile.

Output valid JSON only:
{
  "risk_tolerance": "low|medium|high",
  "decision_style": "analytical|intuitive|social-consensus|impulsive|avoidant",
  "value_ranking": ["top5", "values", "in", "order", "of", "priority"],
  "strengths": ["3-5", "strengths"],
  "weaknesses": ["3-5", "weaknesses"],
  "cognitive_biases": ["2-4", "likely", "biases"],
  "overconfidence_areas": ["1-3", "areas", "they", "overestimate"],
  "blind_spots": ["2-3", "things", "they", "don't", "see"],
  "raw_summary": "A 3-4 sentence narrative summary of who this person is — their core drives, fears, patterns, and contradictions. Write in second person (you)."
}"""

WHATIF_SYSTEM = """You are a simulation engine. Given a person's personality profile and a "what if" scenario, simulate three parallel paths.

Rules:
- Base your simulation STRICTLY on their personality profile. Don't invent traits they don't have.
- Path A: MOST LIKELY — given who they are, what would probably happen
- Path B: OPTIMAL — if luck breaks their way AND they play to their strengths
- Path C: SHADOW — if their weaknesses and blind spots dominate
- Each path must feel emotionally true, not generic. Include specific details that fit their profile.
- Be honest, not motivational. If the shadow path is dark, show it.
- The closing insight should be something they haven't considered — a perspective shift.

Output valid JSON only:
{
  "personality_summary": "One paragraph: who this person is in the context of this scenario.",
  "paths": [
    {
      "label": "Path A: Most Likely",
      "description": "Narrative of what probably happens. 4-6 sentences. Specific, grounded.",
      "emotional_state": "How they'd feel in this path. One sentence.",
      "key_tradeoffs": ["tradeoff 1", "tradeoff 2"],
      "surprises": ["something unexpected", "something they didn't foresee"]
    },
    {
      "label": "Path B: Optimal",
      "description": "...",
      "emotional_state": "...",
      "key_tradeoffs": ["...", "..."],
      "surprises": ["...", "..."]
    },
    {
      "label": "Path C: Shadow",
      "description": "...",
      "emotional_state": "...",
      "key_tradeoffs": ["...", "..."],
      "surprises": ["...", "..."]
    }
  ],
  "bias_analysis": "What cognitive biases affect their view of this scenario? 2-3 sentences.",
  "uncertainty_map": "What they control, what's luck, what they're blind to. 3 bullets.",
  "closing_insight": "One powerful sentence that reframes the scenario."
}"""

# ─── Onboarding ──────────────────────────────────────────────────

async def get_next_question(history: list[dict]) -> str:
    """Given the Q&A history, generate the next interview question."""
    if len(history) == 0:
        return "What's a decision you made that changed everything — the one where, if you'd chosen differently, you'd be a different person today?"

    # Build prompt from history
    transcript = "\n".join([
        f"Q: {h['question']}\nA: {h['answer']}" for h in history
    ])

    prompt = f"""Here's the conversation so far:

{transcript}

Ask the next question. Make it follow naturally from their last answer. If they were vulnerable, go a little deeper. If they were factual, ask about feelings. One question only."""

    response = await chat(prompt, system=INTERVIEWER_SYSTEM, temperature=0.8, max_tokens=150)
    return extract_text(response).strip().strip('"')


# ─── Personality Extraction ──────────────────────────────────────

async def extract_personality(qa_history: list[dict]) -> PersonalityProfile:
    """From the Q&A transcript, extract a structured personality profile."""
    transcript = "\n\n".join([
        f"Q: {h['question']}\nA: {h['answer']}" for h in qa_history
    ])

    prompt = f"""Here is an interview transcript. Extract a structured personality profile.

INTERVIEW:
{transcript}

Output JSON with the personality profile."""

    response = await chat(prompt, system=PERSONA_EXTRACTOR_SYSTEM, temperature=0.3, max_tokens=1500)
    data = extract_json(extract_text(response))

    profile = PersonalityProfile(
        risk_tolerance=data.get("risk_tolerance", "medium"),
        decision_style=data.get("decision_style", ""),
        value_ranking=data.get("value_ranking", []),
        strengths=data.get("strengths", []),
        weaknesses=data.get("weaknesses", []),
        cognitive_biases=data.get("cognitive_biases", []),
        overconfidence_areas=data.get("overconfidence_areas", []),
        blind_spots=data.get("blind_spots", []),
        onboarding_qa=qa_history,
        raw_summary=data.get("raw_summary", ""),
    )

    # Extract education and career from Q&A
    for h in qa_history:
        q = h.get("question", "").lower()
        if "study" in q or "education" in q:
            profile.education = h.get("answer", "")[:200]
        if "career" in q or "work" in q:
            profile.career_path = h.get("answer", "")[:200]
        if "proud" in q or "achievement" in q:
            profile.proudest_moments.append(h.get("answer", "")[:200])
        if "regret" in q or "door" in q:
            profile.regrets.append(h.get("answer", "")[:200])

    return profile


# ─── What-If Simulation ──────────────────────────────────────────

async def simulate_whatif(profile: PersonalityProfile, scenario: str) -> WhatIfReport:
    """Given a personality profile and a what-if question, simulate parallel paths."""
    prompt = f"""PERSONALITY:
{profile.to_narrative()}

WHAT-IF SCENARIO:
"{scenario}"

Simulate three parallel paths. Be specific, honest, and grounded in their actual personality."""

    response = await chat(prompt, system=WHATIF_SYSTEM, temperature=0.8, max_tokens=3000)
    data = extract_json(extract_text(response))

    paths = []
    for p in data.get("paths", []):
        paths.append(ParallelPath(
            label=p.get("label", ""),
            description=p.get("description", ""),
            emotional_state=p.get("emotional_state", ""),
            key_tradeoffs=p.get("key_tradeoffs", []),
            surprises=p.get("surprises", []),
        ))

    return WhatIfReport(
        scenario=scenario,
        personality_summary=data.get("personality_summary", ""),
        paths=paths,
        bias_analysis=data.get("bias_analysis", ""),
        uncertainty_map=data.get("uncertainty_map", ""),
        closing_insight=data.get("closing_insight", ""),
    )


# ─── Stress Test (from dumate's code) ────────────────────────────

STRESS_TEST_SYSTEM = """You are an idea stress-test panel. Four roles simultaneously interrogate the user's idea:

[VC] = Focus on market size, defensibility, team fit, revenue model
[Customer] = Focus on pain level, switching cost, value proposition
[Competitor] = Focus on how you'd be crushed, why this is easy to copy
[Regulator] = Focus on compliance, liability, ethics, data privacy

Each role asks ONE sharp question. Be brutal but constructive. After all four, synthesize a "survival probability" score (0-100) with 3-sentence verdict."""

async def stress_test_idea(idea: str, context: str = "") -> dict:
    """Run a 4-role stress test on an idea/project. From dumate's parallel_universe.py."""
    prompt = f"""Idea to stress-test: {idea}

Additional context: {context}

Give me the 4-role stress test results."""

    response = await chat(prompt, system=STRESS_TEST_SYSTEM, temperature=0.7, max_tokens=2000)
    text = extract_text(response)

    # Parse roles
    result = {
        "vc_question": "",
        "customer_question": "",
        "competitor_question": "",
        "regulator_question": "",
        "survival_score": 50,
        "verdict": ""
    }

    lines = text.split('\n')
    current_role = None
    for line in lines:
        line = line.strip()
        if '[VC]' in line or 'VC:' in line:
            current_role = 'vc'
        elif '[Customer]' in line or 'Customer:' in line:
            current_role = 'customer'
        elif '[Competitor]' in line or 'Competitor:' in line:
            current_role = 'competitor'
        elif '[Regulator]' in line or 'Regulator:' in line:
            current_role = 'regulator'
        elif 'survival' in line.lower() and any(c.isdigit() for c in line):
            try:
                result["survival_score"] = int(''.join(filter(str.isdigit, line)))
            except:
                pass
        elif current_role and line:
            result[f"{current_role}_question"] += line + " "

    result["verdict"] = text[-500:] if len(text) > 500 else text
    return result


# ─── Streaming Simulation ────────────────────────────────────────

async def simulate_whatif_stream(
    profile: PersonalityProfile, scenario: str
) -> AsyncIterator[str]:
    """Stream the what-if simulation tokens for real-time UI updates."""
    prompt = f"""PERSONALITY:
{profile.to_narrative()}

WHAT-IF SCENARIO:
"{scenario}"

Simulate three parallel paths. Output as JSON."""

    async for token in chat_stream(prompt, system=WHATIF_SYSTEM, temperature=0.8, max_tokens=3000):
        yield token
