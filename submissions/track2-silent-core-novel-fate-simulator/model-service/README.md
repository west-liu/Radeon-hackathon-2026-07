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

### Instance setup (AMD Radeon Cloud)

1. **Image**: Select `AMD OneClick Base` (`amd-oneclick-base:rocm7.2.1-py3.12-v20260416`)
2. **SSH Key**: Paste your `~/.ssh/id_ed25519.pub` content into the SSH Public Key field **before** creating the instance
3. **Model API Key**: Not required — this project runs its own models, not AMD-hosted APIs

### 0. Prerequisites

ROCm must be installed and working:
```bash
rocm-smi                    # Should show your GPU
rocminfo | grep "Name:"     # Should list gfx1100 (or your GPU target)
```

If ROCm is not installed, follow the [AMD ROCm installation guide](https://rocm.docs.amd.com/en/latest/deploy/linux/install.html).

### 1. System dependencies

```bash
sudo apt-get update && sudo apt-get install -y espeak-ng libsndfile1 ffmpeg cmake git curl
```

### 2. Python environment

```bash
python3 -m venv /opt/venv && source /opt/venv/bin/activate
pip install diffusers accelerate kokoro spacy soundfile httpx huggingface_hub uvicorn
python -m spacy download en_core_web_sm
```

### 3. Build llama.cpp with HIP

```bash
git config --global http.sslVerify false
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

> **For users in China:** HuggingFace downloads can be very slow. Use the
> `hf-mirror.com` mirror by setting the `HF_ENDPOINT` environment variable
> **before** running `huggingface-cli`:
> ```bash
> export HF_ENDPOINT=https://hf-mirror.com
> huggingface-cli download Qwen/Qwen3-8B-GGUF Qwen3-8B-Q4_K_M.gguf \
>   --local-dir ./models/Qwen3-8B-GGUF
> ```
> Global users can use the default HuggingFace endpoint without any changes.

### 5. Start all services

> **Important:** `image_service.py`, `tts_service.py`, and `gateway.py` do not
> contain `if __name__ == "__main__"` entry blocks. You **must** use `uvicorn`
> to launch the FastAPI applications. Running `python xxx.py --port` will exit
> immediately without starting the server.

Start services **in order** — each backend must be running before the gateway starts:

```bash
# Terminal 1: LLM
./llama.cpp/build/bin/llama-server \
  --model ./models/Qwen3-8B-GGUF/Qwen3-8B-Q4_K_M.gguf \
  --host 127.0.0.1 --port 8081 \
  --n-gpu-layers 99 \
  --ctx-size 8192 \
  --threads 16 \
  --batch-size 512 \
  --flash-attn on

# Terminal 2: Image
uvicorn image_service:app --host 0.0.0.0 --port 8082

# Terminal 3: TTS
uvicorn tts_service:app --host 0.0.0.0 --port 8083

# Terminal 4: Gateway (clients only need this port)
export SILENT_CORE_API_KEY="test-key"
export SILENT_CORE_INTERNAL_API_KEY="test-key"
export LLM_URL="http://127.0.0.1:8081"
uvicorn gateway:app --host 0.0.0.0 --port 8000
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

## Troubleshooting

Issues encountered during deployment on AMD Radeon Cloud.

### 1. `git clone` SSL certificate verification failed

```
fatal: unable to access 'https://github.com/...': server certificate verification failed.
CAfile: none CRLfile: none
```

**Fix:** Disable SSL verification in the container:
```bash
git config --global http.sslVerify false
```

### 2. `pip install` spaCy model: Invalid wheel filename

```
ERROR: Invalid wheel filename (invalid version): 'en_core_web_sm-any-py3-none-any'
```

**Fix:** Use spacy's own download command instead of a direct pip URL:
```bash
python -m spacy download en_core_web_sm
```

### 3. Services exit immediately with `python xxx.py --port`

```
(venv) root@...:~/model-service# python image_service.py --port 8082
(venv) root@...:~/model-service#     # prompt returns immediately, no server started
```

**Cause:** The three service scripts lack `if __name__ == "__main__"` entry
blocks, so `python xxx.py` runs the module top-to-bottom and exits without
calling `uvicorn.run()`.

**Fix:** Use `uvicorn` directly:
```bash
uvicorn image_service:app --host 0.0.0.0 --port 8082
uvicorn tts_service:app --host 0.0.0.0 --port 8083
uvicorn gateway:app --host 0.0.0.0 --port 8000
```

### 4. Gateway crash: `KeyError: 'SILENT_CORE_INTERNAL_API_KEY'`

```
KeyError: 'SILENT_CORE_INTERNAL_API_KEY'
```

**Cause:** `gateway.py` reads two environment variables at import time. Both
must be set **before** launching uvicorn.

**Fix:**
```bash
export SILENT_CORE_API_KEY="test-key"
export SILENT_CORE_INTERNAL_API_KEY="test-key"
export LLM_URL="http://127.0.0.1:8081"
uvicorn gateway:app --host 0.0.0.0 --port 8000
```

### 5. Gateway returns `Model service unavailable`

```json
{"detail": "Model service unavailable: All connection attempts failed"}
```

**Cause:** Gateway cannot reach the LLM backend. The `LLM_URL` environment
variable is not set, so gateway doesn't know where llama-server is listening.

**Fix:** Set `LLM_URL` before starting gateway:
```bash
export LLM_URL="http://127.0.0.1:8081"
```

Also verify LLM is actually running:
```bash
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8081/health
```

### 6. Checking which services are running

`ss` and `netstat` may not be installed in the container. Use curl instead:
```bash
for port in 8081 8082 8083 8000; do
  code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$port/ 2>/dev/null)
  echo "Port $port: $code"
done
```

Expected results when all services are up:
- `8081`: 415 (llama.cpp rejects GET, but server is alive)
- `8082`: 404 (FastAPI, no root route — check `/docs` for 200)
- `8083`: 404 (same as above)
- `8000`: 404 (same as above)

### 7. SSH connection refused / timed out

**Connection timed out:** The instance IP or port has changed after restart.
Check the AMD Radeon Cloud dashboard for updated SSH connection info.

**Connection refused:** The host is reachable but SSH service is not running
on the specified port. Verify the port number in the dashboard.

**Identity file not accessible:** Use absolute path on Windows:
```cmd
ssh -i C:\Users\<username>\.ssh\id_ed25519 root@<IP> -p <PORT>
```

### 8. `--flash-attn` requires a value

```
error: argument --flash-attn: expected one argument
```

**Fix:** Use `--flash-attn on` (not just `--flash-attn`).
