"""F8-controlled audio recording and Whisper transcription."""

import queue
import threading
from collections.abc import Callable

import numpy as np
import sounddevice as sd
from pynput import keyboard
from pywhispercpp.model import Model

from config import MAX_RECORDING_SECONDS, SAMPLE_RATE
from screen import capture_screenshot
from whisper_utils import transcribe_buffer

# Windows virtual-key code for F8.
_VK_F8 = 0x77


class KeyboardShortcutListener:
    """Basic keyboard shortcut listener helper wrapping pynput keyboard.Listener."""

    def __init__(self, on_press: Callable, on_release: Callable) -> None:
        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)

    def start(self) -> None:
        self.listener.start()

    def stop(self) -> None:
        self.listener.stop()


class PushToTalk:
    """Record while F8 is held; F8 is suppressed on Windows so other apps never see it."""

    def __init__(self, model: Model, on_transcript: Callable[[str, str | None], None]) -> None:
        self.model = model
        self.on_transcript = on_transcript
        self.ui_events: queue.Queue[tuple[str, float | None]] = queue.Queue()
        self.recording = threading.Event()
        self.stop_recording = threading.Event()
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            win32_event_filter=self._win32_event_filter,
        )

    def _win32_event_filter(self, msg: int, data: object) -> bool:
        """Block F8 from reaching any other application on Windows."""
        if getattr(data, "vkCode", None) == _VK_F8:
            self.listener.suppress_event()
        return True

    def start(self) -> None:
        self.listener.start()
        print("Ready. Hold F8 to talk; release F8 to transcribe. Press Ctrl+C to quit.")

    def stop(self) -> None:
        self.stop_recording.set()
        self.listener.stop()

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if key == keyboard.Key.f8 and not self.recording.is_set():
            self.recording.set()
            self.stop_recording.clear()
            threading.Thread(target=self._record, daemon=True, name="audio-recorder").start()

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if key == keyboard.Key.f8:
            self.stop_recording.set()

    def _record(self) -> None:
        self.ui_events.put(("show", None))
        audio_queue: queue.Queue[np.ndarray] = queue.Queue()

        def capture(indata: np.ndarray, frames: int, time: object, status: sd.CallbackFlags) -> None:
            if status:
                print(f"Audio callback status: {status}")
            audio_queue.put(indata.copy())

        chunks: list[np.ndarray] = []
        stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=capture)
        pre_captured_screenshot: str | None = None

        try:
            with stream:
                total_duration = 0.0
                while not self.stop_recording.is_set() and total_duration < MAX_RECORDING_SECONDS:
                    try:
                        chunk = audio_queue.get(timeout=0.05)
                        chunks.append(chunk)
                        rms = float(np.sqrt(np.mean(np.square(chunk))))
                        self.ui_events.put(("level", min(rms * 8, 1.0)))
                        total_duration += len(chunk) / SAMPLE_RATE
                    except queue.Empty:
                        continue

            # Instantly pre-capture screenshot at the exact moment recording stops
            try:
                pre_captured_screenshot = capture_screenshot()
            except Exception as err:
                print(f"Pre-screenshot capture error: {err}")

            self.ui_events.put(("thinking", None))

            if not chunks:
                self.ui_events.put(("hide", None))
                return

            audio = np.concatenate(chunks, axis=0).squeeze()
            transcript = transcribe_buffer(audio, self.model)
            if transcript:
                print(f"GuideAI heard: {transcript}")
                self.on_transcript(transcript, pre_captured_screenshot)
            else:
                self.ui_events.put(("hide", None))
        except Exception as error:
            print(f"Microphone/transcription error: {error}")
            self.ui_events.put(("hide", None))
        finally:
            self.recording.clear()

    @staticmethod
    def get_raw_audio_bytes(chunks: list[np.ndarray]) -> bytes:
        """Convert float32 audio chunks into raw 16-bit PCM bytes."""
        if not chunks:
            return b""
        audio = np.concatenate(chunks, axis=0).squeeze()
        audio = np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)
        return (audio * 32767.0).astype(np.int16).tobytes()
