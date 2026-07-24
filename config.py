"""Application settings kept in one place."""

from pathlib import Path

SAMPLE_RATE = 16_000
MAX_RECORDING_SECONDS = 60

LLAMA_SERVER_URL = "http://127.0.0.1:8080/v1/chat/completions"
LLAMA_SERVER_HEALTH_URL = "http://127.0.0.1:8080/health"
LLAMA_SERVER_MODELS_URL = "http://127.0.0.1:8080/v1/models"
# The local llama.cpp server accepts any client-visible model label.
LLAMA_MODEL = "gemma-4-e2b-local"
GGUF_MODEL_PATH = Path(r"D:\Program Files\LocalFlow\data\models\gemma-4-E2B-it-UD-Q4_K_XL.gguf")
MMPROJ_MODEL_PATH = Path(r"D:\Projects\GuideAI\mmproj-BF16.gguf")
LLAMA_SERVER_PATH = Path(r"D:\Program Files\LocalFlow\lib\llama-server.exe")
LLAMA_START_TIMEOUT_SECONDS = 180
LLAMA_REQUEST_TIMEOUT_SECONDS = 180

OVERLAY_DURATION_MS = 8_000
