# Silent Core Model Service

The three AI models behind Novel Fate Simulator, served through one
OpenAI-compatible API gateway. Clients use stable model IDs:
`silent-core/llm`, `silent-core/image`, `silent-core/tts`.

## Models

| Model | Implementation | Compute | Role |
|---|---|---|---|
| `silent-core/llm` | Qwen3-8B Q4_K_M, llama.cpp HIP | AMD Radeon GPU | Narrative generation, agent reasoning |
| `silent-core/image` | Z-Image-Turbo, Diffusers CPU offload | AMD Radeon GPU | Scene illustration |
| `silent-core/tts` | Kokoro-82M, PyTorch | 16 CPU threads | English voice narration |

TTS runs on CPU so it does not contend with LLM and image workloads on the GPU.
The quantized LLM uses ~1/3 of the BF16 memory and reaches ~91.6 tok/s.

## API

```
POST /v1/chat/completions    # LLM text generation
POST /v1/responses            # LLM with structured output
POST /v1/images/generations   # Scene illustration
POST /v1/audio/speech         # Voice narration
GET  /v1/models               # List available models
GET  /health                  # Health check
```

All `/v1/*` requests require `Authorization: Bearer $API_KEY`.

See `examples/python_client.py` for chat, image, and speech client code.

## Deployment

### Hardware

- AMD Radeon GPU with ROCm (tested: gfx1100, 48 GB VRAM)
- Ubuntu 22.04, ROCm 7.2+
- ~30 GB storage for models + tools

### 0. Prerequisites

ROCm must be installed and working:
```bash
rocm-smi                    # Should show your GPU
rocminfo | grep "Name:"     # Should list gfx1100 (or your GPU target)
```

If ROCm is not installed, follow the [AMD ROCm installation guide](https://rocm.docs.amd.com/en/latest/deploy/linux/install.html).

### 1. System dependencies

```bash
sudo apt-get install -y espeak-ng libsndfile1 ffmpeg cmake git curl
```

### 2. Python environment

```bash
python3 -m venv /opt/venv && source /opt/venv/bin/activate
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

Replace `gfx1100` with your GPU target (`rocm_agent_enumerator` to find it).

### 4. Download models

```bash
huggingface-cli download Qwen/Qwen3-8B-GGUF Qwen3-8B-Q4_K_M.gguf \
  --local-dir ./models/Qwen3-8B-GGUF
# Image (Z-Image-Turbo) and TTS (Kokoro-82M) auto-download on first request
```

### 5. Start all services

```bash
# Terminal 1: LLM
./llama.cpp/build/bin/llama-server \
  --model ./models/Qwen3-8B-GGUF/Qwen3-8B-Q4_K_M.gguf \
  --host 127.0.0.1 --port 8081 --n-gpu-layers 99

# Terminal 2: Image
python image_service.py --port 8082

# Terminal 3: TTS
python tts_service.py --port 8083

# Terminal 4: Gateway (clients only need this port)
python gateway.py --port 8000
```

### Smoke test

```bash
# Health
curl http://127.0.0.1:8000/health

# LLM
curl -H "Authorization: Bearer test-key" -H "Content-Type: application/json" \
  http://127.0.0.1:8000/v1/chat/completions \
  -d '{"model":"silent-core/llm","messages":[{"role":"user","content":"Say hello."}],"max_tokens":16}'

# Image (10-30s on first call)
curl -H "Authorization: Bearer test-key" -H "Content-Type: application/json" \
  http://127.0.0.1:8000/v1/images/generations \
  -d '{"model":"silent-core/image","prompt":"A silver compass on an ancient map","size":"512x512"}'

# TTS
curl -H "Authorization: Bearer test-key" -H "Content-Type: application/json" \
  http://127.0.0.1:8000/v1/audio/speech \
  -d '{"model":"silent-core/tts","voice":"heart","input":"Silent Core is ready."}' --output test.wav
```

## Performance

| Workload | Metric | Value |
|---|---|---|
| LLM decode | tokens/s | ~91.6 |
| LLM TTFT | ms | ~42 |
| Image (warm) | seconds | ~10.8 |
| TTS | real-time factor | ~0.51 |

Detailed methodology in `PERFORMANCE_RESULTS.md` and
`RADEON_INFERENCE_OPTIMIZATION_REPORT.md`.

## Client setup

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://PUBLIC_HOST/v1",
    api_key="sc_...",
    timeout=600,
)
```

Image generation is serialized on the single GPU; use a timeout of at
least 300 seconds.

The current `trycloudflare.com` URL is a temporary demo tunnel. Replace
with a named tunnel or direct HTTPS for production.
