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

# Allow environment overrides for portability. If not set, fall back to cross-platform defaults.
LLAMA_SERVER_URL = os.getenv("LLAMA_SERVER_URL", "http://127.0.0.1:8080/v1/chat/completions")
LLAMA_SERVER_HEALTH_URL = os.getenv("LLAMA_SERVER_HEALTH_URL", "http://127.0.0.1:8080/health")
LLAMA_SERVER_MODELS_URL = os.getenv("LLAMA_SERVER_MODELS_URL", "http://127.0.0.1:8080/v1/models")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "gemma-4-e2b-local")
LLAMA_HF_REPO = os.getenv("LLAMA_HF_REPO", "")  # e.g. "unsloth/gemma-4-E2B-it-GGUF:Q4_K_M"

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

# Ollama runtime configurations (used by ollama_manager.py)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma-4-e2b-local")
OLLAMA_START_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_START_TIMEOUT_SECONDS", "60"))
OLLAMA_TAGS_URL = os.getenv("OLLAMA_TAGS_URL", "http://127.0.0.1:11434/api/tags")

# Visual focus spotlight configuration
ENABLE_SPOTLIGHT = os.getenv("ENABLE_SPOTLIGHT", "true").lower() in ("true", "1", "yes")

OVERLAY_DURATION_MS = 8_000
UI_FONT_FAMILY = "Segoe UI" if IS_WINDOWS else "DejaVu Sans"

# Screenshot compression settings.
SCREENSHOT_MAX_WIDTH = 1280
SCREENSHOT_MAX_HEIGHT = 720
SCREENSHOT_JPEG_QUALITY = 50


def validate_hotkey_config(hotkey_name: str = "f8") -> bool:
    """Validate hotkey string configuration name."""
    if not isinstance(hotkey_name, str) or not hotkey_name.strip():
        return False
    valid_keys = {"f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "space", "ctrl", "alt"}
    return hotkey_name.lower().strip() in valid_keys


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
