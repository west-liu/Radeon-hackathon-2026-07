# Model Deployment Guide — Silent Core API

Deploy the three AI models behind Novel Fate Simulator on an AMD Radeon GPU.

## Hardware Requirements

| Component | Minimum |
|---|---|
| GPU | AMD Radeon with ROCm support (tested: gfx1100, 48 GB VRAM) |
| VRAM | 48 GB (three models share the same GPU) |
| OS | Ubuntu 22.04 with ROCm 7.2+ |
| Storage | ~30 GB for models + tools |

## Architecture

```
Port :8000  ┌─────────────────────────────────────────┐
◄──────────►│           API Gateway (gateway.py)       │
            │  /v1/chat/completions → LLM   (:8081)   │
            │  /v1/images/generations → Image (:8082) │
            │  /v1/audio/speech      → TTS   (:8083)  │
            └─────────────────────────────────────────┘
```

All three models run behind one OpenAI-compatible endpoint. Clients use stable
model IDs: `silent-core/llm`, `silent-core/image`, `silent-core/tts`.

## Quick Deploy (5 Steps)

### 1. Install system dependencies

```bash
sudo apt-get update
sudo apt-get install -y espeak-ng libsndfile1 ffmpeg cmake git curl
```

### 2. Set up Python environment

```bash
python3 -m venv /opt/venv
source /opt/venv/bin/activate
pip install --upgrade pip

# Core dependencies
pip install diffusers accelerate kokoro spacy soundfile httpx huggingface_hub
pip install https://hf-mirror.com/spacy/en_core_web_sm/resolve/main/en_core_web_sm-any-py3-none-any.whl
```

### 3. Build llama.cpp with HIP

```bash
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
cmake -B build -DGGML_HIP=ON -DAMDGPU_TARGETS=gfx1100 -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 8 --target llama-server llama-bench
```

If your GPU target is different, replace `gfx1100` with your GPU's target (run
`rocm_agent_enumerator` to find it).

### 4. Download models

```bash
# LLM: Qwen3-8B (quantized, ~5 GB)
huggingface-cli download Qwen/Qwen3-8B-GGUF Qwen3-8B-Q4_K_M.gguf \
  --local-dir ./models/Qwen3-8B-GGUF

# Image: Z-Image-Turbo (auto-downloaded on first request)
# TTS: Kokoro-82M (auto-downloaded on first request)
```

### 5. Start services

```bash
# Start each model service (run in separate terminals or use tmux)

# Terminal 1: LLM service
./llama.cpp/build/bin/llama-server \
  --model ./models/Qwen3-8B-GGUF/Qwen3-8B-Q4_K_M.gguf \
  --host 127.0.0.1 --port 8081 --n-gpu-layers 99

# Terminal 2: Image service
python image_service.py --port 8082

# Terminal 3: TTS service
python tts_service.py --port 8083

# Terminal 4: API Gateway (the only port clients need)
python gateway.py --port 8000
```

## Verify (Smoke Test)

```bash
# Health check
curl http://127.0.0.1:8000/health

# List available models
curl -H "Authorization: Bearer test-key" http://127.0.0.1:8000/v1/models

# Test LLM
curl -H "Authorization: Bearer test-key" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8000/v1/chat/completions \
  -d '{"model":"silent-core/llm","messages":[{"role":"user","content":"Say hello."}],"max_tokens":16}'

# Test Image (may take 10–30 seconds on first call)
curl -H "Authorization: Bearer test-key" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8000/v1/images/generations \
  -d '{"model":"silent-core/image","prompt":"A silver compass on an ancient map","size":"512x512"}'

# Test TTS
curl -H "Authorization: Bearer test-key" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8000/v1/audio/speech \
  -d '{"model":"silent-core/tts","voice":"heart","input":"Silent Core is ready."}' \
  --output test.wav
```

## Expected Performance

| Workload | Metric | Value |
|---|---|---|
| LLM decode | tokens/second | ~91.6 |
| LLM time-to-first-token | ms | ~42 |
| Image (warm) | seconds | ~10.8 |
| TTS | real-time factor | ~0.51 |

See `PERFORMANCE_RESULTS.md` and `RADEON_INFERENCE_OPTIMIZATION_REPORT.md`
for methodology and full before/after data.

## Troubleshooting

**"HIP not found"**: Verify ROCm is installed: `rocm-smi`. Check that llama.cpp
was compiled with `-DGGML_HIP=ON`.

**"Out of memory"**: The three-model setup requires ~48 GB VRAM. If you have
less, run only the services you need (e.g., LLM only).

**Image generation times out (>300s)**: First image call loads the model from
disk (cold start). Subsequent calls are much faster. Increase the client timeout
to 600 seconds for the first request.

**Port conflicts**: Change `--port` on each start script. Update `gateway.py`
upstream targets to match.
