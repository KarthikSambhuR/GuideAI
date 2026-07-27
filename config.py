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

LLAMA_SERVER_URL = os.getenv("LLAMA_SERVER_URL", "http://127.0.0.1:8080/v1/chat/completions")
LLAMA_SERVER_HEALTH_URL = os.getenv("LLAMA_SERVER_HEALTH_URL", "http://127.0.0.1:8080/health")
LLAMA_SERVER_MODELS_URL = os.getenv("LLAMA_SERVER_MODELS_URL", "http://127.0.0.1:8080/v1/models")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "gemma-4-e2b-local")

# Path configuration with env var overrides and platform defaults
default_gguf = (
    r"D:\Program Files\LocalFlow\data\models\gemma-4-E2B-it-UD-Q4_K_XL.gguf"
    if IS_WINDOWS else str(Path.home() / ".cache" / "guideai" / "models" / "gemma-4-E2B-it-UD-Q4_K_XL.gguf")
)
default_mmproj = (
    r"D:\Projects\GuideAI\mmproj-BF16.gguf"
    if IS_WINDOWS else str(Path.home() / ".cache" / "guideai" / "models" / "mmproj-BF16.gguf")
)
default_server_bin = (
    r"D:\Program Files\LocalFlow\lib\llama-server.exe"
    if IS_WINDOWS else "llama-server"
)

GGUF_MODEL_PATH = Path(os.getenv("GGUF_MODEL_PATH", default_gguf))
MMPROJ_MODEL_PATH = Path(os.getenv("MMPROJ_MODEL_PATH", default_mmproj))
LLAMA_SERVER_PATH = Path(os.getenv("LLAMA_SERVER_PATH", default_server_bin))

LLAMA_START_TIMEOUT_SECONDS = int(os.getenv("LLAMA_START_TIMEOUT_SECONDS", "180"))
LLAMA_REQUEST_TIMEOUT_SECONDS = int(os.getenv("LLAMA_REQUEST_TIMEOUT_SECONDS", "180"))
LLAMA_GPU_LAYERS = int(os.getenv("LLAMA_GPU_LAYERS", "99"))

OVERLAY_DURATION_MS = 8_000


UI_FONT_FAMILY = "Segoe UI" if IS_WINDOWS else "DejaVu Sans"
