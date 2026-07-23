"""F8-controlled audio recording and Whisper transcription."""

import queue
import threading
from collections.abc import Callable

import numpy as np
import sounddevice as sd
from pynput import keyboard
from pywhispercpp.model import Model

from config import MAX_RECORDING_SECONDS, SAMPLE_RATE


class PushToTalk:
    """Record while F8 is held and immediately free F8 after transcription."""

    def __init__(self, model: Model, on_transcript: Callable[[str], None]) -> None:
        self.model = model
        self.on_transcript = on_transcript
        self.ui_events: queue.Queue[tuple[str, float | None]] = queue.Queue()
        self.recording = threading.Event()
        self.stop_recording = threading.Event()
        self.listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)

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
        chunks: list[np.ndarray] = []
        self.ui_events.put(("show", None))

        def capture(indata: np.ndarray, frames: int, time: object, status: sd.CallbackFlags) -> None:
            if status:
                print(f"Audio status: {status}")
            chunk = indata.copy()
            chunks.append(chunk)
            rms = float(np.sqrt(np.mean(np.square(chunk))))
            self.ui_events.put(("level", min(rms * 8, 1.0)))

        try:
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=capture):
                self.stop_recording.wait(MAX_RECORDING_SECONDS)
            self.ui_events.put(("hide", None))
            if not chunks:
                return
            audio = np.concatenate(chunks, axis=0).squeeze()
            audio = np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)
            peak = np.max(np.abs(audio))
            if peak:
                audio /= peak
            transcript = " ".join(segment.text for segment in self.model.transcribe(audio)).strip()
            if transcript:
                print(f"GuideAI heard: {transcript}")
                self.on_transcript(transcript)
        except Exception as error:
            print(f"Microphone/transcription error: {error}")
        finally:
            self.ui_events.put(("hide", None))
            self.recording.clear()
