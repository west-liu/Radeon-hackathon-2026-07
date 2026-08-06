# Hello E World — Project Specification

**Track 2**: Development & Local Deployment of Private AI Agents
**Team**: west-liu
**Date**: August 6, 2026

---

## 1. Application Scenarios

### Primary: Personal Decision Support
A user facing a major life decision (career change, relocation, relationship, education) talks to Hello E World for 5 minutes. Hello E World builds a personality model and simulates three parallel life paths for their scenario.

### Secondary: Long-term Life Planning
Beyond single decisions — users can model 3-year and 5-year trajectories based on different career, financial, and lifestyle choices. Personality-aware planning, not generic advice.

### Future: Talent & Team Matching
Personality profiles as a basis for complementary team formation, co-founder matching, and role fit assessment. Not resume screening — compatibility discovery.

---

## 2. Agent Architecture

```
┌──────────────────────────────────────────────────┐
│                  User Interface                    │
│       Chat-based, one question at a time           │
│       Dark theme, sidebar with session state        │
└──────────────────────┬───────────────────────────┘
                       │ HTTP REST + SSE
┌──────────────────────▼───────────────────────────┐
│              FastAPI Server (port 8080)            │
│                                                    │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │  Interviewer │  │  Personality  │  │  What-If  │ │
│  │   Module     │  │   Extractor   │  │ Simulator │ │
│  │              │  │               │  │           │ │
│  │ Generates    │  │ Extracts 16-  │  │ Generates │ │
│  │ contextual   │  │ dimension     │  │ 3 parallel│ │
│  │ follow-up    │  │ profile from  │  │ life paths│ │
│  │ questions    │  │ Q&A history   │  │ + biases  │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘ │
│         │                  │                 │       │
│         └──────────────────┴─────────────────┘       │
│                          │                           │
│              ┌───────────▼──────────┐               │
│              │   Session Manager    │               │
│              │   (in-memory →       │               │
│              │    SQLite planned)   │               │
│              └──────────────────────┘               │
└──────────────────────┬───────────────────────────┘
                       │ httpx (OpenAI-compatible)
┌──────────────────────▼───────────────────────────┐
│              vLLM Server (port 8000)               │
│       Qwen/Qwen2.5-14B-Instruct                   │
│       AMD Radeon Pro W7900 · 48GB VRAM             │
│       ROCm 7.2.1 · gfx1100                         │
└──────────────────────────────────────────────────┘
```

### Agent Properties

| Property | Implementation |
|----------|---------------|
| **Memory** | Q&A history stored in session state; personality profile persists; RAG for embedding-based retrieval (planned) |
| **Planning** | Three-path simulation with bias analysis and uncertainty mapping |
| **Tool Calling** | Personality extraction API, simulation API, health check with GPU info |
| **Privacy** | All data in-memory per session; SQLite for persistence; no network egress |

---

## 3. Core Capabilities

### 3.1 Conversational Onboarding
- Adaptive question generation based on conversation history
- 16 predefined question pool across 7 categories (background, decision, values, risk, social, self, future)
- Natural follow-up logic — goes deeper when user is open, pivots when guarded
- Minimum 3 Q&A pairs for personality extraction; recommended 5-10

### 3.2 Personality Extraction
16-dimension profile:
- **Risk tolerance**: low / medium / high
- **Decision style**: analytical / intuitive / social-consensus / impulsive / avoidant
- **Value ranking**: top 5 values
- **Strengths & Weaknesses**: 3-5 each
- **Cognitive biases**: 2-4 identified patterns
- **Overconfidence areas**: 1-3 domains
- **Blind spots**: 2-3 things they don't see about themselves
- **Narrative summary**: 3-4 sentence psychographic profile

### 3.3 What-If Simulation
For any scenario input, generates:
- **Path A (Most Likely)**: Probabilistic projection based on personality traits
- **Path B (Optimal)**: If strengths are leveraged and luck breaks favorably
- **Path C (Shadow)**: If blind spots and cognitive biases dominate
- **Bias Analysis**: Cognitive biases affecting the user's view of this scenario
- **Uncertainty Map**: What's controllable, what's luck, what's invisible
- **Closing Insight**: One reframing perspective the user hasn't considered

### 3.4 Demo Mode
Pre-loaded 6 Q&A pairs (tech entrepreneur persona) for instant demonstration without onboarding.

---

## 4. Model & Local Deployment

### Model Selection
| Model | VRAM | W7900 Fit | Quality | Speed |
|-------|------|-----------|---------|-------|
| **Qwen2.5-14B-Instruct** | ~28GB | ✅ (20GB headroom) | Excellent CN+EN | 40-60 tok/s |
| Qwen2.5-32B-Instruct | ~64GB | ❌ (exceeds 48GB) | Superior | N/A |
| Qwen3.6-35B-A3B | ~70GB | ❌ | Best | N/A |

**Chosen**: Qwen2.5-14B-Instruct — the only model that fits W7900 48GB with production-quality output.

### vLLM Configuration
```bash
vllm serve Qwen/Qwen2.5-14B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90 \
  --dtype auto
```

### Deployment Stack
- **OS**: Ubuntu 24.04
- **GPU Driver**: ROCm 7.2.1 (gfx1100)
- **Inference**: vLLM 0.26.0
- **Backend**: FastAPI + uvicorn
- **Model Format**: HuggingFace safetensors
- **Storage**: `/workspace/persistent/` (survives instance restarts)

---

## 5. Inference Optimization on AMD Radeon GPU

### 5.1 ROCm-specific Optimizations
- PyTorch `2.10.0+rocm7.0` compiled for gfx1100 architecture
- triton-rocm 3.6.0 for kernel-level optimizations
- HIP graph capture enabled for repeated inference patterns

### 5.2 Memory Optimization
- `--gpu-memory-utilization 0.90` leaves 4.8GB buffer for KV cache
- `--max-model-len 8192` limits context to prevent OOM
- Single model loading (no dual-model architecture)
- In-memory session state (no database overhead for MVP)

### 5.3 Performance Targets
| Metric | Target |
|--------|--------|
| Token generation | 40-60 tok/s |
| Personality extraction | <15s for 6 Q&A pairs |
| What-if simulation | <30s for full 3-path report |
| Model load time | <60s from vLLM start |
| VRAM utilization | <90% (43.2GB) |

### 5.4 Fallback Strategy
If vLLM on W7900 encounters compatibility issues:
- AMD Token Factory API (Qwen3.6-35B-A3B) at developer.amd.com.cn
- Already implemented as `VLLMClient` with OpenAI-compatible interface
- Same API contract — zero code changes in agent logic

---

## 6. Privacy & Security

- **All inference local**: No API calls to external services
- **Session isolation**: In-memory state per session, cleared on reset
- **No telemetry**: Zero data collection or phoning home
- **Persistent storage**: SQLite with optional encryption (planned)
- **User control**: Full reset endpoint clears all data immediately

---

## 7. Evaluation Criteria Alignment

| Official Criterion | Hello E World Implementation |
|--------------------|------------------------|
| Application scenarios | Personal decisions, life planning, team matching |
| Agent architecture diagram | See Section 2 |
| Core capabilities | Conversational onboarding, personality extraction, what-if simulation |
| Model & local deployment | Qwen2.5-14B on W7900 via vLLM, full deployment guide |
| Inference optimization | ROCm-specific PyTorch, triton-rocm, HIP graphs, memory tuning |
| Source code | Complete at `helloeworld/source/` with README |
| Demo video | 3:30 scripted demonstration with GPU evidence |
| Supplementary | PPT/Poster |
