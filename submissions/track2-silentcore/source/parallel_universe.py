"""Core Parallel Universe simulation engine."""
import json
from typing import List, Dict, Any, Optional
from dataclasses import asdict

import config
import prompts
from vllm_client import VLLMClient
from personality_engine import PersonalityEngine, PersonalityProfile
from rag_engine import get_rag

class ParallelUniverseEngine:
    def __init__(self):
        self.client = VLLMClient()
        self.personality = PersonalityEngine(config.PERSONALITY_DB_PATH)
        self.rag = get_rag(config.CHROMA_DB_PATH)

    def learn(self, user_id: str, notes: List[str]) -> PersonalityProfile:
        """Step 1: Learn user personality from notes."""
        # Fallback rule-based extraction
        profile = self.personality.analyze(user_id, notes)

        # If LLM available, enhance with LLM
        try:
            health = self.client.health()
            if health.get("ok"):
                text = "\n".join(notes[:20])  # First 20 notes
                prompt = f"Analyze this person's personality from their notes:\n\n{text[:4000]}\n\n" + \
                        "Extract: risk_tolerance (0-1), social_preference (0-1), career_drive (0-1), " + \
                        "location_attachment (0-1), decision_style (analytical/intuitive/emotional), " + \
                        "key_values (list), strengths (list), weaknesses (list), past_regrets (list). " + \
                        "Output ONLY JSON."
                llm_result = self.client.chat(
                    system=prompts.PERSONALITY_EXTRACTION_SYSTEM,
                    user=prompt,
                    json_mode=True
                )
                # Merge LLM insights with rule-based
                try:
                    llm_data = json.loads(llm_result)
                    for k, v in llm_data.items():
                        if hasattr(profile, k) and v is not None:
                            setattr(profile, k, v)
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass

        # Store in RAG
        self.rag.add_memories(user_id, notes, [{"type": "diary"} for _ in notes])
        self.personality._save()
        return profile

    def simulate(self, user_id: str, decision: str, n: int = None, depth: int = None) -> List[Dict[str, Any]]:
        """Step 2: Generate parallel universes for a decision point."""
        n = n or config.UNIVERSE_COUNT
        depth = depth or config.SIMULATION_DEPTH

        profile = self.personality.get(user_id)
        if not profile:
            raise ValueError(f"No personality profile found for user {user_id}. Run learn() first.")

        # Retrieve relevant memories
        memories = self.rag.query(user_id, decision, n_results=10)
        context = "\n".join([m["text"] for m in memories[:5]])

        prompt = f"""User personality: {json.dumps(asdict(profile), ensure_ascii=False)}

Decision point: {decision}

Relevant past context: {context}

Generate {n} parallel universes where the user made different choices at this decision point.
For each universe, simulate forward {depth} years.
Show: the alternative choice, key events, how personality traits evolved, and life satisfaction (0-10).
"""

        try:
            result = self.client.chat(
                system=prompts.UNIVERSE_GENERATION_SYSTEM,
                user=prompt
            )
            universes = self._parse_universes(result)
        except Exception as e:
            universes = [{"name": "Universe A", "choice": decision, "events": [f"Error: {str(e)}"], "satisfaction": 5}]

        return universes

    def stress_test(self, idea: str, context: str = "") -> Dict[str, Any]:
        """Step 3: Four-role idea stress test."""
        prompt = f"Idea to stress-test: {idea}\n\nAdditional context: {context}"

        try:
            result = self.client.chat(
                system=prompts.STRESS_TEST_SYSTEM,
                user=prompt
            )
            return self._parse_stress_test(result)
        except Exception as e:
            return {
                "vc_question": "What is your addressable market?",
                "customer_question": "Why should I switch?",
                "competitor_question": "We can build this in 2 weeks.",
                "regulator_question": "Is user data stored locally?",
                "survival_score": 50,
                "verdict": f"Stress test completed with fallback (error: {e})"
            }

    def compare(self, user_id: str, universes: List[Dict[str, Any]]) -> str:
        """Step 4: Generate comparison table."""
        prompt = f"""Compare these parallel universe outcomes for the user:

{json.dumps(universes, ensure_ascii=False, indent=2)}

Generate a structured comparison and a final verdict paragraph.
"""
        try:
            return self.client.chat(
                system=prompts.COMPARISON_TABLE_SYSTEM,
                user=prompt
            )
        except Exception:
            return "Comparison generation failed. Use raw universe data."

    def _parse_universes(self, text: str) -> List[Dict[str, Any]]:
        """Parse numbered universe list from LLM output."""
        lines = text.strip().split('\n')
        universes = []
        current = None

        for line in lines:
            line = line.strip()
            if line.startswith('**Universe') or line.startswith('Universe'):
                if current:
                    universes.append(current)
                current = {"name": line, "choice": "", "events": [], "satisfaction": 5}
            elif current and line:
                if 'satisfaction' in line.lower() or 'score' in line.lower():
                    try:
                        current["satisfaction"] = int(''.join(filter(str.isdigit, line)))
                    except:
                        pass
                else:
                    current["events"].append(line)

        if current:
            universes.append(current)

        if not universes:
            universes = [{"name": "Universe 1", "choice": "Default path", "events": [text[:500]], "satisfaction": 5}]

        return universes

    def _parse_stress_test(self, text: str) -> Dict[str, Any]:
        """Parse stress test output into structured format."""
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
