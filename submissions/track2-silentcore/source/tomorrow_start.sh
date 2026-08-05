#!/bin/bash
# tomorrow_start.sh — One-command startup for Parallel Universe Simulator
# Run this AFTER overnight install completes (PyTorch + vLLM + model ready)

set -e
LOG="/workspace/persistent/tomorrow_start.log"
> "$LOG"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG"
}

VENV="/workspace/persistent/venv/bin/activate"
CODE_DIR="/workspace/persistent/code/source"
MODEL_DIR="/workspace/persistent/models"

log "=== TOMORROW START ==="

# 1. Activate venv
log "Step 1: Activating virtual environment..."
source "$VENV"

# 2. Verify GPU
log "Step 2: Verifying GPU..."
GPU=$(python -c "import torch; print('GPU:' if torch.cuda.is_available() else 'NO GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')" 2>&1)
log "$GPU"

if [[ "$GPU" == *"NO GPU"* ]]; then
    log "ERROR: GPU not detected. Check PyTorch ROCm installation."
    log "Run: pip uninstall -y torch torchvision torchaudio && pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.2"
    exit 1
fi

# 3. Check vLLM
log "Step 3: Checking vLLM..."
if ! pip list 2>/dev/null | grep -q "^vllm"; then
    log "vLLM not found. Installing..."
    pip install vllm >> "$LOG" 2>&1
fi
log "vLLM OK"

# 4. Check model
log "Step 4: Checking model..."
if [ ! -d "$MODEL_DIR/models--Qwen--Qwen2.5-14B-Instruct" ] && [ ! -d "$MODEL_DIR/Qwen/Qwen2.5-14B-Instruct" ]; then
    log "Model not found. Downloading..."
    export HF_ENDPOINT=https://hf-mirror.com
    pip install huggingface_hub >> "$LOG" 2>&1
    nohup python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen2.5-14B-Instruct', cache_dir='$MODEL_DIR', max_workers=8)" >> "$LOG" 2>&1 &
    log "Model download started in background. Wait 30-60 minutes, then re-run this script."
    exit 0
fi
log "Model OK"

# 5. Install Agent deps
log "Step 5: Installing Agent dependencies..."
cd "$CODE_DIR"
pip install -r requirements.txt >> "$LOG" 2>&1
log "Agent deps OK"

# 6. Start vLLM server
log "Step 6: Starting vLLM..."
if ! curl -s http://localhost:8000/v1/models >/dev/null 2>&1; then
    nohup vllm serve Qwen/Qwen2.5-14B-Instruct --host 0.0.0.0 --port 8000 --max-model-len 8192 --gpu-memory-utilization 0.85 > /workspace/persistent/vllm_server.log 2>&1 &
    log "vLLM starting... waiting 20s"
    sleep 20
else
    log "vLLM already running"
fi

# 7. Verify vLLM
log "Step 7: Verifying vLLM..."
MODELS=$(curl -s http://localhost:8000/v1/models 2>/dev/null | head -c 200)
if [ -n "$MODELS" ]; then
    log "vLLM OK: $MODELS"
else
    log "WARNING: vLLM may not be fully ready. Check /workspace/persistent/vllm_server.log"
fi

# 8. Start Agent API
log "Step 8: Starting Agent API..."
nohup python main.py > /workspace/persistent/agent_api.log 2>&1 &
log "Agent API started on port 8080"

# 9. Wait and verify
log "Step 9: Verifying Agent API..."
sleep 3
HEALTH=$(curl -s http://localhost:8080/health 2>/dev/null)
if [ -n "$HEALTH" ]; then
    log "Agent API OK: $HEALTH"
else
    log "WARNING: Agent API may not be ready. Check /workspace/persistent/agent_api.log"
fi

# 10. Print summary
log "=== ALL SERVICES STARTED ==="
cat <<'SUMMARY'

╔══════════════════════════════════════════════════════════════╗
║           Parallel Universe Simulator — READY                  ║
╠══════════════════════════════════════════════════════════════╣
║  vLLM Server:     http://localhost:8000                      ║
║  Agent API:       http://localhost:8080                    ║
║  Health Check:    curl http://localhost:8080/health        ║
║                                                                ║
║  Test Commands:                                                ║
║  curl http://localhost:8080/health                          ║
║  curl -X POST http://localhost:8080/learn \                ║
║    -H "Content-Type: application/json" \                     ║
║    -d '{"user_id":"demo","notes":["I am cautious"]}'       ║
╚══════════════════════════════════════════════════════════════╝

SUMMARY

log "Check logs: tail -f /workspace/persistent/tomorrow_start.log"
