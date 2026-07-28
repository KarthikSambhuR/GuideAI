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
GGUF_MODEL_PATH = Path(os.getenv("GGUF_MODEL_PATH", r"C:\Users\eren\GuideAI\GuideAI\models\unsloth-gemma-4-E2B-it-GGUF\MTP\mtp-gemma-4-E2B-it-Q8_0.gguf"))
MMPROJ_MODEL_PATH = Path(os.getenv("MMPROJ_MODEL_PATH", r"C:\Users\eren\GuideAI\GuideAI\models\unsloth-gemma-4-E2B-it-GGUF\MTP\mtp-gemma-4-E2B-it-BF16.gguf"))
LLAMA_SERVER_PATH = Path(os.getenv("LLAMA_SERVER_PATH", r"C:\Users\eren\GuideAI\GuideAI\bin\llama-server.exe"))
LLAMA_START_TIMEOUT_SECONDS = int(os.getenv("LLAMA_START_TIMEOUT_SECONDS", "180"))
LLAMA_REQUEST_TIMEOUT_SECONDS = int(os.getenv("LLAMA_REQUEST_TIMEOUT_SECONDS", "180"))

OVERLAY_DURATION_MS = 8_000

# Screenshot compression settings.
# Reduce these to speed up LLM requests at the cost of visual detail.
# Increase SCREENSHOT_JPEG_QUALITY (1-95) for sharper images.
SCREENSHOT_MAX_WIDTH = 1280
SCREENSHOT_MAX_HEIGHT = 720
SCREENSHOT_JPEG_QUALITY = 50

UI_FONT_FAMILY = "Segoe UI" if IS_WINDOWS else "DejaVu Sans"
