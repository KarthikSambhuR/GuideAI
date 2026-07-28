"""Application settings kept in one place."""

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

IS_WINDOWS = sys.platform == "win32"

SAMPLE_RATE = 16_000
MAX_RECORDING_SECONDS = 60

# Allow environment overrides for portability. If not set, fall back to the previous defaults.
LLAMA_SERVER_URL = os.getenv("LLAMA_SERVER_URL", "http://127.0.0.1:8080/v1/chat/completions")
LLAMA_SERVER_HEALTH_URL = os.getenv("LLAMA_SERVER_HEALTH_URL", "http://127.0.0.1:8080/health")
LLAMA_SERVER_MODELS_URL = os.getenv("LLAMA_SERVER_MODELS_URL", "http://127.0.0.1:8080/v1/models")
# The local llama.cpp server accepts any client-visible model label.
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "gemma-4-e2b-local")
LLAMA_HF_REPO = os.getenv("LLAMA_HF_REPO", "")  # e.g. "unsloth/gemma-4-E2B-it-GGUF:Q4_K_M"
GGUF_MODEL_PATH = Path(os.getenv("GGUF_MODEL_PATH", r"C:\Users\eren\GuideAI\GuideAI\models\unsloth-gemma-4-E2B-it-GGUF\MTP\mtp-gemma-4-E2B-it-Q8_0.gguf"))
MMPROJ_MODEL_PATH = Path(os.getenv("MMPROJ_MODEL_PATH", r"C:\Users\eren\GuideAI\GuideAI\models\unsloth-gemma-4-E2B-it-GGUF\MTP\mtp-gemma-4-E2B-it-BF16.gguf"))
LLAMA_SERVER_PATH = Path(os.getenv("LLAMA_SERVER_PATH", r"C:\Users\eren\GuideAI\GuideAI\bin\llama-server.exe"))
LLAMA_START_TIMEOUT_SECONDS = int(os.getenv("LLAMA_START_TIMEOUT_SECONDS", "180"))
LLAMA_REQUEST_TIMEOUT_SECONDS = int(os.getenv("LLAMA_REQUEST_TIMEOUT_SECONDS", "180"))

# Number of model layers to offload to GPU via llama.cpp -ngl flag.
# Set to 0 to disable GPU offloading (CPU-only). Set to 99 to offload all layers.
LLAMA_GPU_LAYERS = int(os.getenv("LLAMA_GPU_LAYERS", "99"))

# Ollama runtime configurations (used by ollama_manager.py)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma-4-e2b-local")
OLLAMA_START_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_START_TIMEOUT_SECONDS", "60"))
OLLAMA_TAGS_URL = os.getenv("OLLAMA_TAGS_URL", "http://127.0.0.1:11434/api/tags")

OVERLAY_DURATION_MS = 8_000
UI_FONT_FAMILY = "Segoe UI" if IS_WINDOWS else "DejaVu Sans"

# Screenshot compression settings.
# Reduce these to speed up LLM requests at the cost of visual detail.
# Increase SCREENSHOT_JPEG_QUALITY (1-95) for sharper images.
SCREENSHOT_MAX_WIDTH = 1280
SCREENSHOT_MAX_HEIGHT = 720
SCREENSHOT_JPEG_QUALITY = 50


class ConfigManager:
    """Central configuration manager providing validated runtime settings."""

    def __init__(self) -> None:
        self.sample_rate = SAMPLE_RATE
        self.max_recording_seconds = MAX_RECORDING_SECONDS
        self.llama_url = LLAMA_SERVER_URL
        self.model_name = LLAMA_MODEL

    def get(self, key: str, default: object = None) -> object:
        return getattr(self, key, default)


config_manager = ConfigManager()