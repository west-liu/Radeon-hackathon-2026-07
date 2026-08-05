# Parallel Universe Simulator

**Track 2 — Private AI Agent Development & Local Deployment**
**Team**: SilentCore (west-liu)

---

## What Is This?

A **local AI agent** that reads your personal notes/diary, learns your personality, and simulates alternative life paths — all running on your own GPU. Your private thoughts never leave your machine.

**Demo scenario**: "If I had taken that offer at the startup in 2022, what would my life look like in 2025?" — The agent generates 3 parallel universe timelines, each shaped by your actual personality traits extracted from your notes.

---

## Why Local?

Your diary contains your deepest regrets, fears, and dreams. Uploading this to cloud LLMs is a privacy disaster. This project proves you can run **14B-parameter models locally** on AMD ROCm hardware and get meaningful, personal AI without data exposure.

---

## Architecture

```
User Notes (Markdown/Diary)
    |
    v
Personality Engine — rule-based + LLM-enhanced extraction
    |
    v
RAG Memory (ChromaDB) — vector storage of life events
    |
    v
Parallel Universe Simulator — 3 universes × 5 years forward
    |
    v
Idea Stress Test — 4-role panel (VC/Customer/Competitor/Regulator)
    |
    v
Comparison Table + Verdict
```

---

## Tech Stack

| Layer | Tech |
|---|---|
| Inference | vLLM + Qwen2.5-14B-Instruct on AMD Radeon Pro W7900 |
| Framework | FastAPI |
| Memory | ChromaDB (vector) + JSON (personality profiles) |
| GPU Runtime | ROCm 7.2.1 + PyTorch ROCm 6.2 |
| Fallback | Rule-based engine when LLM unavailable |

---

## Quick Start

```bash
# 1. Start vLLM
vllm serve Qwen/Qwen2.5-14B-Instruct --host 0.0.0.0 --port 8000

# 2. Start API
pip install -r source/requirements.txt
cd source
python main.py

# 3. Test
curl http://localhost:8080/health
curl -X POST http://localhost:8080/learn \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","notes":["I always choose stability over risk","I regret not taking the startup offer","My friends say I overthink everything"]}'
```

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | LLM + system health |
| `/learn` | POST | Feed notes, extract personality |
| `/personality/{id}` | GET | Retrieve profile |
| `/simulate` | POST | Generate parallel universes |
| `/stress-test` | POST | 4-role idea interrogation |
| `/compare` | POST | Comparison table + verdict |

---

## Files

```
track2-silentcore/
  source/
    config.py            — Environment & model config
    personality_engine.py — Trait extraction + persistence
    rag_engine.py        — ChromaDB vector memory
    vllm_client.py       — OpenAI-compatible client
    prompts.py           — System prompts (4 roles)
    parallel_universe.py — Core simulation engine
    main.py              — FastAPI server + CLI
    requirements.txt
  docs/
    README.md
    TECH_SPEC.md
    DEPLOYMENT.md
  demo/
    demo_script.md      — Video narration
    demo_data.json      — Sample input/output
  evidence/
    gpu_screenshot.png  — ROCm + vLLM running
```

---

## Privacy Guarantee

- All data stored in `/workspace/persistent/` (local disk)
- ChromaDB runs locally, no external vector DB
- vLLM serves from local model weights
- No API keys, no cloud calls
