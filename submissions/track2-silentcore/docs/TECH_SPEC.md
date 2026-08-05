# Technical Specification — Parallel Universe Simulator

---

## 1. Overview

Private AI agent that runs entirely on AMD ROCm hardware. No cloud dependency. Two core capabilities:

1. **Parallel Universe Simulation** — Learn personality from notes → generate alternative life paths
2. **Idea Stress Test** — 4-role adversarial panel interrogates any idea

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                          │
│              (curl / Postman / Frontend)                    │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP
┌─────────────────────────▼───────────────────────────────────┐
│              FastAPI Server (Port 8080)                     │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │ /learn      │  │ /simulate    │  │ /stress-test    │    │
│  │ /personality│  │ /compare     │  │                 │    │
│  └─────────────┘  └──────────────┘  └─────────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼──────┐ ┌───────▼──────┐ ┌───────▼──────┐
│ Personality  │ │    RAG       │ │  vLLM Client │
│   Engine     │ │  (ChromaDB)  │ │   (httpx)    │
└──────────────┘ └──────────────┘ └──────────────┘
        │                 │                 │
        └─────────────────┴─────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│              vLLM Inference Server (Port 8000)              │
│           Qwen2.5-14B-Instruct on AMD W7900                 │
│                    ROCm 7.2.1 / gfx1100                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Personality Engine

### 3.1 Dimensions Extracted

| Dimension | Scale | Source |
|---|---|---|
| risk_tolerance | 0-1 | Risk/safe keyword frequency |
| social_preference | 0-1 | Social/solo keyword frequency |
| career_drive | 0-1 | Ambition/balance keywords |
| location_attachment | 0-1 | Mobility/home keywords |
| decision_style | analytical/intuitive/emotional | LLM classification |
| key_values | List[str] | LLM extraction |
| strengths | List[str] | LLM extraction |
| weaknesses | List[str] | LLM extraction |
| past_regrets | List[str] | LLM extraction |

### 3.2 Dual-Mode Extraction

- **Rule-based** (always works): Keyword counting with polarity scoring
- **LLM-enhanced** (when GPU available): Qwen 14B parses free text into structured JSON

### 3.3 Storage

- Personality profiles: JSON file (`personality_db.json`)
- Raw memories: ChromaDB vector store (`chromadb/`)

---

## 4. RAG Engine

### 4.1 Vector Store

- **Backend**: ChromaDB (PersistentClient)
- **Embedding**: Sentence-transformers (all-MiniLM-L6-v2)
- **Distance**: Cosine similarity
- **Fallback**: In-memory keyword search when ChromaDB unavailable

### 4.2 Memory Lifecycle

1. User uploads notes → chunked into sentences
2. Each chunk embedded → stored with metadata (user_id, timestamp, type)
3. Simulation queries: "decision_point" → top-k relevant memories retrieved
4. Retrieved memories injected into LLM prompt as context

---

## 5. Parallel Universe Simulation

### 5.1 Input

- `user_id`: Whose personality to simulate
- `decision`: The fork-in-the-road moment
- `n`: Number of universes (default 3)
- `depth`: Years forward (default 5)

### 5.2 Prompt Engineering

```
System: You are a parallel universe generator...
User: Personality: {json}
      Decision: "Should I move to Shenzhen for the startup offer?"
      Relevant memories: {retrieved_context}
      Generate 3 universes, 5 years forward.
```

### 5.3 Output Format

```json
{
  "universes": [
    {
      "name": "Universe A: The Risk-Taker",
      "choice": "Accepted the offer",
      "events": ["Year 1: Burnout...", "Year 3: Promotion..."],
      "satisfaction": 7
    }
  ]
}
```

---

## 6. Idea Stress Test

### 6.1 Four-Role Panel

| Role | Focus | Example Question |
|---|---|---|
| VC | Market, defensibility, team | "What's your TAM and why are YOU the one to build this?" |
| Customer | Pain, switching cost | "Why should I abandon my current solution?" |
| Competitor | Speed to copy, moat | "Our next release adds this as a free feature." |
| Regulator | Compliance, liability | "Where is user data stored? Can you prove it?" |

### 6.2 Scoring

- LLM generates survival probability (0-100)
- Based on strength of answers to all four roles
- Verdict: 3-sentence synthesis

---

## 7. Hardware Requirements

| Component | Minimum | Optimal |
|---|---|---|
| GPU | AMD W7900 48GB | Same |
| VRAM | 32GB | 48GB |
| System RAM | 64GB | 128GB+ |
| Disk | 100GB SSD | 200GB+ |
| ROCm | 6.2+ | 7.2.1 |

### 7.1 Model Sizing

- Qwen2.5-14B-Instruct: ~28GB weights, ~40GB VRAM at fp16
- W7900 48GB: Fits 14B with room for vLLM KV cache
- If OOM: Reduce `--max-model-len` to 4096, `--gpu-memory-utilization` to 0.8

---

## 8. Fallback Strategy

| Failure Mode | Fallback |
|---|---|
| vLLM won't install | `transformers` + `accelerate` direct inference |
| GPU not recognized | AMD Token Factory API (last resort) |
| ChromaDB fails | InMemoryRAG (keyword search) |
| LLM timeout | Rule-based personality extraction |
| Model download fails | Smaller model: Qwen2.5-7B-Instruct |

---

## 9. Performance Benchmarks

| Operation | Time (W7900) |
|---|---|
| Personality extraction (LLM) | 3-5s |
| Universe generation (3×5yr) | 15-25s |
| Stress test (4 roles) | 8-12s |
| Memory retrieval (RAG) | <100ms |
| API cold start | 2-3s |

---

## 10. Privacy Architecture

```
User Notes
    |
    v (never leaves machine)
Local GPU (AMD W7900)
    |
    v
Local Vector DB (ChromaDB)
    |
    v
Local JSON Profile
```

- No network calls during inference
- No API keys required
- ChromaDB runs as embedded process
- All files in `/workspace/persistent/` (durable storage)

---

## 11. Future Extensions

- Multi-user personality comparison ("What if we had never met?")
- Time-travel simulation ("What if I could warn 2019-me?")
- Decision tree visualization (branching parallel paths)
- Export to Obsidian/Notion as "alternative life journal"
