# RadeonReviewer

On-premise multi-model code-review Agent for AMD Radeon GPU (ROCm / vLLM).

## Quick start

```bash
# 1. install dependencies
pip install -r requirements.txt

# 2. configure (see `config.py`)
export LLM_BASE_URL="http://127.0.0.1:8000/v1"
export MODEL_ID="Qwen/Qwen2.5-14B-Instruct"

# 3. start server
python main.py

# 4. or run CLI review
python main.py <owner> <repo> <pr_number>
```

## Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/review` | POST | Review a GitHub PR by owner/repo/number |
| `/review/diff` | POST | Review raw diff text |
| `/webhook` | POST | GitHub webhook for PR opened/synchronize |
| `/reviews` | GET | List stored reviews |

## Files

- `config.py` — environment-based configuration
- `prompts.py` — system prompt templates for fast / deep / synthesis passes
- `vllm_client.py` — thin OpenAI-compatible client
- `tools.py` — PR diff fetching & parsing
- `agent.py` — three-pass review orchestration
- `main.py` — FastAPI server + CLI entry
