"""Configuration for Parallel Universe Simulator."""
import os

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
MODEL_ID = os.getenv("MODEL_ID", "Qwen/Qwen2.5-14B-Instruct")
MAX_MODEL_LEN = int(os.getenv("MAX_MODEL_LEN", "8192"))
GPU_MEMORY_UTILIZATION = float(os.getenv("GPU_MEMORY_UTILIZATION", "0.85"))

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "/workspace/persistent/chromadb")
PERSONALITY_DB_PATH = os.getenv("PERSONALITY_DB_PATH", "/workspace/persistent/personality_db.json")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))

API_PORT = int(os.getenv("API_PORT", "8080"))
API_HOST = os.getenv("API_HOST", "0.0.0.0")

UNIVERSE_COUNT = int(os.getenv("UNIVERSE_COUNT", "3"))
SIMULATION_DEPTH = int(os.getenv("SIMULATION_DEPTH", "5"))
