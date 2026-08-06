#!/bin/bash
# helloeworld/start.sh — One-command startup for Hello E World
# Adapted from dumate's tomorrow_start.sh
#
# Usage: bash start.sh
# After:  http://localhost:8080

set -e
LOG="/workspace/persistent/helloeworld_start.log"
> "$LOG"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG"
}

VENV_PYTHON="/workspace/persistent/venv/bin/python"
VENV_PIP="/workspace/persistent/venv/bin/pip"
CODE_DIR="/workspace/persistent/helloeworld/source"
MODEL_DIR="/workspace/persistent/models"

log "=== Hello E World Startup ==="

# 1. Verify GPU
log "Step 1: Verifying GPU..."
GPU=$($VENV_PYTHON -c "import torch; print('GPU:' + torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO GPU')" 2>&1)
log "$GPU"

if [[ "$GPU" == *"NO GPU"* ]]; then
    log "ERROR: GPU not detected. Check PyTorch ROCm."
    log "Run: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm7.0"
    exit 1
fi

# 2. Check model
log "Step 2: Checking model..."
MODEL_SIZE=$(du -sh "$MODEL_DIR" 2>/dev/null | cut -f1)
log "Model dir size: $MODEL_SIZE"

if [ ! -d "$MODEL_DIR/models--Qwen--Qwen2.5-14B-Instruct" ]; then
    log "ERROR: Model not found. Download first:"
    log "  export HF_ENDPOINT=https://hf-mirror.com"
    log "  $VENV_PYTHON -c \"from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen2.5-14B-Instruct', cache_dir='$MODEL_DIR', max_workers=8)\""
    exit 1
fi
log "Model OK"

# 3. Install deps
log "Step 3: Installing Hello E World dependencies..."
cd "$CODE_DIR"
$VENV_PIP install -r requirements.txt >> "$LOG" 2>&1
log "Deps OK"

# 4. Start llama.cpp (if not running)
log "Step 4: Starting llama.cpp..."
if ! curl -s http://localhost:8000/v1/models >/dev/null 2>&1; then
    log "llama.cpp not running. Starting..."
    nohup llama-server Qwen/Qwen2.5-14B-Instruct \
        --host 0.0.0.0 --port 8000 \
        --max-model-len 8192 \
        --gpu-memory-utilization 0.90 \
        --dtype auto \
        > /workspace/persistent/llama_server.log 2>&1 &

    log "Waiting for llama.cpp to load model (30-60s)..."
    for i in $(seq 1 60); do
        if curl -s http://localhost:8000/v1/models >/dev/null 2>&1; then
            log "llama.cpp ready after ${i}s"
            break
        fi
        sleep 2
    done
else
    log "llama.cpp already running"
fi

# 5. Verify llama.cpp
log "Step 5: Verifying llama.cpp..."
MODELS=$(curl -s http://localhost:8000/v1/models 2>/dev/null | head -c 300)
if [ -n "$MODELS" ]; then
    log "llama.cpp OK"
else
    log "WARNING: llama.cpp may not be ready. Check /workspace/persistent/llama_server.log"
fi

# 6. Start Hello E World API
log "Step 6: Starting Hello E World API..."
# Kill old instance if any
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 1

cd "$CODE_DIR"
LLAMA_BASE="http://127.0.0.1:8000/v1" \
nohup $VENV_PYTHON -m uvicorn main:app --host 0.0.0.0 --port 8080 \
    > /workspace/persistent/helloeworld_api.log 2>&1 &
log "Hello E World API starting..."

# 7. Verify
log "Step 7: Verifying Hello E World API..."
sleep 3
HEALTH=$(curl -s http://localhost:8080/health 2>/dev/null)
if [ -n "$HEALTH" ]; then
    log "Hello E World API OK: $HEALTH"
else
    log "WARNING: API not responding. Check /workspace/persistent/helloeworld_api.log"
fi

# 8. Summary
log "=== Hello E World READY ==="
cat <<'SUMMARY'

╔══════════════════════════════════════════════════════════════╗
║              🔮 Hello E World — Ready                              ║
╠══════════════════════════════════════════════════════════════╣
║  llama.cpp Server:     http://localhost:8000                      ║
║  Hello E World API:    http://localhost:8080                      ║
║  Frontend:        http://localhost:8080                      ║
║                                                              ║
║  Quick test:                                                 ║
║  curl http://localhost:8080/health                           ║
║  curl -X POST http://localhost:8080/demo/quick-start         ║
║                                                              ║
║  Logs:                                                       ║
║  tail -f /workspace/persistent/llama_server.log               ║
║  tail -f /workspace/persistent/helloeworld_api.log              ║
║  tail -f /workspace/persistent/helloeworld_start.log             ║
╚══════════════════════════════════════════════════════════════╝

SUMMARY
