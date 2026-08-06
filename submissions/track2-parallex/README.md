# Parallex — Parallel Universe Simulator

> **5 minutes of conversation. Your personality model. Three parallel lives for every decision.**

Parallex is a private, local-first AI agent that builds your personality profile through natural conversation, then simulates what your life would look like if you made different choices — all running on an AMD Radeon GPU.

**Track 2**: Development & Local Deployment of Private AI Agents
**Team**: west-liu
**Hardware**: AMD Radeon Pro W7900 (48GB VRAM) + ROCm 7.2.1

---

## What It Does

1. **Talk** — AI interviewer asks 5-10 conversational questions. Not a form. Not a chatbot. Feels like talking to a perceptive friend.

2. **Understand** — Extracts a 16-dimension personality profile: risk tolerance, decision style, values, strengths, blind spots, cognitive biases.

3. **Simulate** — Input any "what-if" question. Parallex simulates three parallel paths:
   - **Path A (Most Likely)**: Given who you are, what probably happens
   - **Path B (Optimal)**: If luck breaks your way and you play to your strengths
   - **Path C (Shadow)**: If your blind spots and weaknesses dominate

4. **Insight** — Bias analysis, uncertainty map, and a closing insight that reframes the scenario.

---

## Quick Start

```bash
# 1. Start vLLM server (model must be downloaded)
vllm serve Qwen/Qwen2.5-14B-Instruct \
  --host 0.0.0.0 --port 8000 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90

# 2. Start Parallex API
cd parallex/source
pip install -r requirements.txt
VLLM_BASE=http://127.0.0.1:8000/v1 uvicorn main:app --host 0.0.0.0 --port 8080

# 3. Open browser
# http://localhost:8080
```

## Demo Mode

Click "⚡ Demo" — 6 preloaded Q&A pairs demonstrate the full flow in under 90 seconds.

---

## Architecture

```
Browser (index.html)
    │  Chat UI - one question at a time
    ▼
FastAPI Server (port 8080)
    │  Session management, personality extraction, simulation
    ▼
vLLM Server (port 8000)
    │  Qwen2.5-14B-Instruct on AMD Radeon Pro W7900
    ▼
SQLite (local) — All data stays on this machine
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Chat UI frontend |
| GET | `/health` | GPU status, session state |
| GET | `/onboard/next-question` | Get next interview question |
| POST | `/onboard/answer` | Submit an answer |
| POST | `/personality/extract` | Build personality profile |
| POST | `/simulate` | Run what-if simulation |
| POST | `/simulate/stream` | Streaming simulation (SSE) |
| POST | `/demo/quick-start` | Load demo Q&A |
| POST | `/reset` | Clear session |

---

## Why This Can Win

- **0 competitors** in Track 2 (57 projects analyzed, zero what-if/personality simulators)
- **100% local inference** — vLLM on W7900, no API calls, data never leaves the machine
- **Agent properties** — memory (Q&A history), planning (3-path simulation), tool calling (personality extraction API)
- **Privacy-first** — all conversations and personality models stored locally in SQLite
- **Emotionally compelling** — not another code reviewer, not another contract analyzer

---

## Team

**West Liu** — Solo developer. Product, backend, frontend, deployment.

---

## License

MIT
