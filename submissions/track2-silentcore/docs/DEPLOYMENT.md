# Deployment Guide — Parallel Universe Simulator

## Hardware

- AMD Radeon Pro W7900, 48GB VRAM, gfx1100
- ROCm 7.2.1, Ubuntu 24.04, Python 3.12.3
- Server: 36.150.116.206:31285 (root)
- Persistent storage: /workspace/persistent

## Step 1: PyTorch ROCm

```bash
source /workspace/persistent/venv/bin/activate
pip uninstall -y torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.2
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

## Step 2: vLLM

```bash
pip install vllm
```

## Step 3: Download Model

```bash
export HF_ENDPOINT=https://hf-mirror.com
pip install huggingface_hub
nohup python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen2.5-14B-Instruct', cache_dir='/workspace/persistent/models', max_workers=8)" > /workspace/persistent/model_download.log 2>&1 &
```

## Step 4: Start vLLM

```bash
vllm serve Qwen/Qwen2.5-14B-Instruct --host 0.0.0.0 --port 8000 --max-model-len 8192 --gpu-memory-utilization 0.85 > /workspace/persistent/vllm_server.log 2>&1 &
curl http://localhost:8000/v1/models
```

## Step 5: Upload & Start Agent

```bash
# From local machine
scp -P 31285 -r source root@36.150.116.206:/workspace/persistent/code/

# On server
cd /workspace/persistent/code/source
pip install -r requirements.txt
python main.py &
```

## Step 6: Test

```bash
curl http://localhost:8080/health
curl -X POST http://localhost:8080/learn -H "Content-Type: application/json" -d '{"user_id":"demo","notes":["I always choose stability","I regret not taking the startup offer"]}'
curl -X POST http://localhost:8080/simulate -H "Content-Type: application/json" -d '{"user_id":"demo","decision":"Should I move to Shenzhen for a startup?"}'
```

## Troubleshooting

| Issue | Fix |
|---|---|
| GPU not detected | Check `rocm-smi`, reinstall PyTorch ROCm |
| vLLM install fails | `pip install vllm --no-deps` + manual deps |
| OOM | Reduce `--max-model-len` to 4096, `--gpu-memory-utilization` to 0.8 |
| Model download slow | `HF_ENDPOINT=https://hf-mirror.com` |
| ChromaDB import error | `pip install chromadb` or fallback to InMemoryRAG |
