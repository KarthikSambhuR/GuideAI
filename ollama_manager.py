"""Start and validate the local Ollama runtime used by GuideAI."""

import json
import shutil
import subprocess
import tempfile
import time
from urllib.error import URLError
from urllib.request import urlopen

from config import GGUF_MODEL_PATH, OLLAMA_MODEL, OLLAMA_START_TIMEOUT_SECONDS, OLLAMA_TAGS_URL


class OllamaManager:
    """Ensure Ollama and the selected local model are available before use."""

    def __init__(self) -> None:
        self.executable = shutil.which("ollama")
        self.process: subprocess.Popen[bytes] | None = None

    def ensure_ready(self) -> None:
        """Start Ollama if necessary and import the configured local GGUF once."""
        if not self._is_running():
            self._start_server()
        if not self._model_is_available():
            self._import_local_model()

    def stop(self) -> None:
        """Stop only the Ollama process launched by this app."""
        if self.process and self.process.poll() is None:
            self.process.terminate()

    def _is_running(self) -> bool:
        try:
            with urlopen(OLLAMA_TAGS_URL, timeout=1) as response:
                return response.status == 200
        except URLError:
            return False

    def _start_server(self) -> None:
        if not self.executable:
            raise RuntimeError(
                "Ollama is not installed or is not on PATH. Install Ollama, then run app.py again."
            )
        print("Starting the local Ollama server...")
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self.process = subprocess.Popen(
            [self.executable, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
        deadline = time.monotonic() + OLLAMA_START_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if self._is_running():
                return
            if self.process.poll() is not None:
                break
            time.sleep(0.25)
        raise RuntimeError("Ollama did not start. Open Ollama once, then run app.py again.")

    def _model_is_available(self) -> bool:
        with urlopen(OLLAMA_TAGS_URL, timeout=3) as response:
            data = json.load(response)
        models = data.get("models", [])
        return any(model.get("name") == OLLAMA_MODEL for model in models)

    def _import_local_model(self) -> None:
        if not self.executable:
            raise RuntimeError("Ollama is not installed, so the local Gemma model cannot be imported.")
        if not GGUF_MODEL_PATH.is_file():
            raise RuntimeError(f"The configured GGUF model was not found: {GGUF_MODEL_PATH}")
        print(f"Importing local GGUF as {OLLAMA_MODEL}. This happens once...")
        modelfile_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", suffix=".Modelfile", delete=False,
            ) as modelfile:
                modelfile.write(f'FROM "{GGUF_MODEL_PATH}"\n')
                modelfile_path = modelfile.name
            subprocess.run(
                [self.executable, "create", OLLAMA_MODEL, "-f", modelfile_path],
                check=True,
            )
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"Could not import {OLLAMA_MODEL}: {error}") from error
        finally:
            if modelfile_path:
                try:
                    Path(modelfile_path).unlink(missing_ok=True)
                except OSError:
                    pass
