"""Start and validate the local llama.cpp vision server used by GuideAI."""

import shutil
import subprocess
import time
from urllib.error import URLError
from urllib.request import urlopen

from config import (
    GGUF_MODEL_PATH,
    IS_WINDOWS,
    LLAMA_GPU_LAYERS,
    LLAMA_SERVER_MODELS_URL,
    LLAMA_SERVER_PATH,
    LLAMA_START_TIMEOUT_SECONDS,
    MMPROJ_MODEL_PATH,
)


class LlamaManager:
    """Run the bundled llama.cpp server with Gemma's vision projector."""

    def __init__(self) -> None:
        self.process: subprocess.Popen[bytes] | None = None

    def ensure_ready(self) -> None:
        if not GGUF_MODEL_PATH.is_file():
            raise RuntimeError(f"The Gemma GGUF was not found: {GGUF_MODEL_PATH}")
        if not MMPROJ_MODEL_PATH.is_file():
            raise RuntimeError(f"The vision projector was not found: {MMPROJ_MODEL_PATH}")

        server_bin = str(LLAMA_SERVER_PATH)
        if not LLAMA_SERVER_PATH.is_file() and not shutil.which(server_bin):
            raise RuntimeError(f"llama-server executable was not found at {LLAMA_SERVER_PATH} or on PATH.")

        if not self._is_running():
            self._start_server()

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()

    @staticmethod
    def _is_running() -> bool:
        """Return true only after llama.cpp has finished loading the model."""
        try:
            # /health can return 200 while the model is still loading. The models
            # endpoint returns 503 until it is safe to send a screenshot request.
            with urlopen(LLAMA_SERVER_MODELS_URL, timeout=1) as response:
                return response.status == 200
        except URLError:
            return False

    def _start_server(self) -> None:
        print(f"Starting llama.cpp with Gemma 4 image support (GPU layers: {LLAMA_GPU_LAYERS})...")
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if IS_WINDOWS else 0
        server_cmd = str(LLAMA_SERVER_PATH) if LLAMA_SERVER_PATH.is_file() else (shutil.which(str(LLAMA_SERVER_PATH)) or str(LLAMA_SERVER_PATH))
        cmd = [
            server_cmd,
            "--model", str(GGUF_MODEL_PATH),
            "--mmproj", str(MMPROJ_MODEL_PATH),
            "--host", "127.0.0.1",
            "--port", "8080",
            "--jinja",
        ]
        if LLAMA_GPU_LAYERS > 0:
            cmd.extend(["-ngl", str(LLAMA_GPU_LAYERS)])
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )

        deadline = time.monotonic() + LLAMA_START_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if self._is_running():
                return
            if self.process.poll() is not None:
                break
            time.sleep(0.25)
        raise RuntimeError("llama.cpp did not start. Check that port 8080 is available.")
