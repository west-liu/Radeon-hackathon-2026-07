# RadeonReviewer

**AMD AI DevMaster Hackathon 2026 — Track 2: Development & Local Deployment of Private AI Agents**

**Participant:** West Liu (`west-liu`)

**Application:** RadeonReviewer
**Research question:** *How can a locally deployed multi-model LLM agent bring human-quality code review to every pull request while keeping source code entirely on-premise?*

RadeonReviewer is a locally-deployed Agentic AI system for automated code review. It runs entirely on AMD Radeon GPU hardware via vLLM, processes GitHub pull-request diffs through a **fast scan → deep analysis → synthesis** three-pass pipeline, and produces structured review reports. Because all inference happens on local GPU, no source code ever leaves the machine — a critical privacy guarantee for enterprise codebases.

## Submission deliverables

| Requirement | Deliverable |
|---|---|
| Project specification | [`PROJECT_SPEC.md`](PROJECT_SPEC.md) |
| Source code | [`source/`](source/) |
| Reproduction / deployment guide | [`RADEON_CLOUD_DEPLOYMENT.md`](RADEON_CLOUD_DEPLOYMENT.md) and [`source/README.md`](source/README.md) |
| Demo video | `demo/RadeonReviewer_Track2_Demo_EN.mp4` — (to be recorded) |
| Radeon run evidence | `evidence/vllm_run/` — (to be collected after server deployment) |

## Official Track 2 compliance map

| Official requirement | Exact review location |
|---|---|
| Application scenarios | `PROJECT_SPEC.md`, Section 1 |
| Agent architecture diagram | `PROJECT_SPEC.md`, Section 2 |
| Introduction to core capabilities | `PROJECT_SPEC.md`, Sections 3–4 |
| Model introduction and local deployment plan | `PROJECT_SPEC.md`, Section 5; `RADEON_CLOUD_DEPLOYMENT.md` |
| AMD Radeon inference-speed optimization | `PROJECT_SPEC.md`, Section 6; raw run evidence |
| Complete source repository | [`source/`](source/) |
| Environment, startup guide, dependencies | This README and [`source/README.md`](source/README.md) |
| 3–5 minute actual-operation demo | Demo video (to be recorded) |

## Quick start

See [`source/README.md`](source/README.md) for detailed setup and API usage.

```bash
cd source/
pip install -r requirements.txt
export LLM_BASE_URL="http://127.0.0.1:8000/v1"
python main.py        # starts FastAPI server on :8080
```

## Architecture at a glance

```
GitHub Webhook (PR opened)
        |
        v
FastAPI Server (port 8080)
        |
   +----+----+
   |         |
   v         v
vLLM:14B   vLLM:32B  (or single model with dual prompts)
(fast)     (deep)
   |         |
   +----+----+
        |
        v
SQLite Review DB  →  Markdown Report  →  PR Comment / SSE Stream
```

## Hardware provenance

All LLM inference runs on AMD Radeon Pro W7900 (48 GB VRAM) in the official Radeon Cloud instance provided by the hackathon. ROCm 7.2.1, PyTorch (ROCm), and vLLM are installed from source or wheels compiled for `gfx1100`.
