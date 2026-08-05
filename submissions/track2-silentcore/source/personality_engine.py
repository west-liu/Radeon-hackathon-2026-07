"""Personality modeling engine — learns user traits from notes/diary."""
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class PersonalityProfile:
    risk_tolerance: float = 0.5          # 0=cautious, 1=adventurous
    social_preference: float = 0.5       # 0=introvert, 1=extrovert
    career_drive: float = 0.5            # 0=work-life balance, 1=ambition
    location_attachment: float = 0.5     # 0=mobile, 1=rooted
    decision_style: str = "analytical"   # analytical / intuitive / emotional
    key_values: List[str] = None
    past_regrets: List[str] = None
    strengths: List[str] = None
    weaknesses: List[str] = None

    def __post_init__(self):
        if self.key_values is None: self.key_values = []
        if self.past_regrets is None: self.past_regrets = []
        if self.strengths is None: self.strengths = []
        if self.weaknesses is None: self.weaknesses = []

class PersonalityEngine:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.profiles: Dict[str, PersonalityProfile] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for uid, p in data.items():
                    self.profiles[uid] = PersonalityProfile(**p)

    def _save(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump({uid: asdict(p) for uid, p in self.profiles.items()}, f, ensure_ascii=False, indent=2)

    def analyze(self, user_id: str, notes: List[str]) -> PersonalityProfile:
        """Extract personality dimensions from free-text notes."""
        text = "\n".join(notes)
        profile = PersonalityProfile()

        # Rule-based extraction (fallback when LLM unavailable)
        risky_words = ['冒险', '冒险', '跳', '创业', '裸辞', '激进', '激进', 'break', 'quit', 'startup']
        safe_words = ['稳定', '稳定', '保守', '保守', '谨慎', '谨慎', 'safe', 'steady', 'cautious']
        social_words = ['社交', '社交', '聚会', '聚会', '团队', '团队', '合作', '合作', 'social', 'team']
        solo_words = ['独处', '独处', '安静', '安静', '独立', '独立', 'alone', 'solo', 'quiet']

        risk_score = sum(1 for w in risky_words if w in text) - sum(1 for w in safe_words if w in text)
        social_score = sum(1 for w in social_words if w in text) - sum(1 for w in solo_words if w in text)

        profile.risk_tolerance = max(0.0, min(1.0, 0.5 + risk_score * 0.1))
        profile.social_preference = max(0.0, min(1.0, 0.5 + social_score * 0.1))
        profile.key_values = self._extract_keywords(text)
        self.profiles[user_id] = profile
        self._save()
        return profile

    def _extract_keywords(self, text: str) -> List[str]:
        # Simple keyword extraction — LLM will do this better in production
        return list(set([w.strip('，。！？,.!?') for w in text.split() if len(w) > 2]))[:20]

    def get(self, user_id: str) -> Optional[PersonalityProfile]:
        return self.profiles.get(user_id)
