"""
Parallex — Data Structures
Personality Profile, What-If Scenario, Parallel Path
"""

from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class PersonalityProfile:
    """Extracted from onboarding conversation."""
    # Core traits
    risk_tolerance: str = ""          # low / medium / high
    decision_style: str = ""          # analytical / intuitive / social-consensus
    value_ranking: list[str] = field(default_factory=list)  # top 5 values
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)

    # Life context
    education: str = ""
    career_path: str = ""
    key_decisions: list[dict] = field(default_factory=list)  # [{decision, outcome, feeling}]
    regrets: list[str] = field(default_factory=list)
    proudest_moments: list[str] = field(default_factory=list)

    # Meta
    cognitive_biases: list[str] = field(default_factory=list)  # detected biases
    overconfidence_areas: list[str] = field(default_factory=list)
    blind_spots: list[str] = field(default_factory=list)

    # Raw
    onboarding_qa: list[dict] = field(default_factory=list)  # [{question, answer}]
    raw_summary: str = ""  # AI-generated narrative summary

    def to_dict(self) -> dict:
        return {
            "risk_tolerance": self.risk_tolerance,
            "decision_style": self.decision_style,
            "value_ranking": self.value_ranking,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "education": self.education,
            "career_path": self.career_path,
            "key_decisions": self.key_decisions,
            "regrets": self.regrets,
            "proudest_moments": self.proudest_moments,
            "cognitive_biases": self.cognitive_biases,
            "overconfidence_areas": self.overconfidence_areas,
            "blind_spots": self.blind_spots,
            "raw_summary": self.raw_summary,
        }

    def to_narrative(self) -> str:
        """Convert profile to a compact narrative for prompt context."""
        return f"""
PERSONALITY PROFILE:
Risk tolerance: {self.risk_tolerance}
Decision style: {self.decision_style}
Top values: {', '.join(self.value_ranking)}
Strengths: {', '.join(self.strengths)}
Weaknesses: {', '.join(self.weaknesses)}
Education: {self.education}
Career: {self.career_path}
Key decisions: {json.dumps(self.key_decisions, ensure_ascii=False)}
Regrets: {', '.join(self.regrets)}
Proudest: {', '.join(self.proudest_moments)}
Biases: {', '.join(self.cognitive_biases)}
Blind spots: {', '.join(self.blind_spots)}
"""


@dataclass
class ParallelPath:
    """A single simulated life path."""
    label: str = ""            # "Path A: Most Likely"
    description: str = ""      # narrative description
    emotional_state: str = ""  # how you'd feel
    key_tradeoffs: list[str] = field(default_factory=list)
    surprises: list[str] = field(default_factory=list)  # unexpected outcomes

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "description": self.description,
            "emotional_state": self.emotional_state,
            "key_tradeoffs": self.key_tradeoffs,
            "surprises": self.surprises,
        }


@dataclass
class WhatIfReport:
    """Complete simulation report."""
    scenario: str  # the user's what-if question
    personality_summary: str  # brief who-you-are
    paths: list[ParallelPath] = field(default_factory=list)
    bias_analysis: str = ""  # what biases affect your view of this scenario
    uncertainty_map: str = ""  # what you control vs what's luck
    closing_insight: str = ""  # one powerful closing line

    def to_dict(self) -> dict:
        return {
            "scenario": self.scenario,
            "personality_summary": self.personality_summary,
            "paths": [p.to_dict() for p in self.paths],
            "bias_analysis": self.bias_analysis,
            "uncertainty_map": self.uncertainty_map,
            "closing_insight": self.closing_insight,
        }

    def format_markdown(self) -> str:
        lines = [
            f"# 🔮 Parallex — What-If Report",
            f"",
            f"**Scenario:** {self.scenario}",
            f"",
            f"---",
            f"",
            f"## 🧠 Who You Are",
            f"",
            self.personality_summary,
            f"",
            f"---",
            f"",
        ]
        for p in self.paths:
            lines.append(f"## {p.label}")
            lines.append(f"")
            lines.append(p.description)
            lines.append(f"")
            lines.append(f"**Emotional State:** {p.emotional_state}")
            lines.append(f"")
            lines.append(f"**Key Tradeoffs:**")
            for t in p.key_tradeoffs:
                lines.append(f"- {t}")
            lines.append(f"")
            lines.append(f"**Surprises:**")
            for s in p.surprises:
                lines.append(f"- {s}")
            lines.append(f"")
            lines.append(f"---")
            lines.append(f"")

        lines.append(f"## 🎯 Bias Analysis")
        lines.append(f"")
        lines.append(self.bias_analysis)
        lines.append(f"")
        lines.append(f"## 📊 Uncertainty Map")
        lines.append(f"")
        lines.append(self.uncertainty_map)
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")
        lines.append(f"## 💫 Closing Insight")
        lines.append(f"")
        lines.append(f"> {self.closing_insight}")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"*Parallex — See every version of yourself. Powered by AMD Radeon GPU + ROCm.*")

        return "\n".join(lines)


# ─── Onboarding questions (dynamic, not all asked) ──────────────

ONBOARDING_POOL = [
    # Education & Background
    {"id": "edu", "question": "What did you study, and did you choose it or was it chosen for you?", "category": "background"},
    {"id": "career", "question": "Walk me through your career so far — what's the through-line, if any?", "category": "background"},

    # Decision Style
    {"id": "big_decision", "question": "Tell me about the biggest decision you've ever made. How did you make it?", "category": "decision"},
    {"id": "decision_style", "question": "When you're stuck between two choices, what do you usually do? Wait, research, ask friends, flip a coin?", "category": "decision"},

    # Values
    {"id": "values", "question": "What are five things you value most in life? Don't overthink — first five that come to mind.", "category": "values"},
    {"id": "value_conflict", "question": "When have two of your values been in direct conflict? What did you do?", "category": "values"},

    # Risk
    {"id": "risk", "question": "What's the riskiest thing you've ever done? Would you do it again?", "category": "risk"},
    {"id": "failure", "question": "Tell me about a time you failed badly. What actually happened, and what story do you tell yourself about it?", "category": "risk"},

    # Relationships & Social
    {"id": "social", "question": "Who are the three people who've shaped you most? What did each give you?", "category": "social"},
    {"id": "conflict", "question": "How do you handle conflict? Avoid it, lean in, or something else?", "category": "social"},

    # Self-Perception
    {"id": "strength", "question": "What are you really good at — not what your resume says, but what people actually come to you for?", "category": "self"},
    {"id": "weakness", "question": "What's your worst trait? Be honest — no one else will see this.", "category": "self"},
    {"id": "blind_spot", "question": "What's something about yourself that you only realized recently — that others probably knew all along?", "category": "self"},

    # Regret & Future
    {"id": "regret", "question": "Is there a door you didn't walk through that you still think about? Which one?", "category": "future"},
    {"id": "future_self", "question": "If you met yourself ten years from now, what would you want them to tell you?", "category": "future"},
]
