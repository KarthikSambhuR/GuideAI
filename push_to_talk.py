"""F8-controlled audio recording and Whisper transcription."""

import queue
import threading
from collections.abc import Callable

import numpy as np
import sounddevice as sd
from pynput import keyboard
from pywhispercpp.model import Model

from config import MAX_RECORDING_SECONDS, SAMPLE_RATE
from whisper_utils import transcribe_buffer

# Windows virtual-key code for F8.
_VK_F8 = 0x77


class PushToTalk:
    """Record while F8 is held; F8 is suppressed so other apps never see it."""

    def __init__(self, model: Model, on_transcript: Callable[[str], None]) -> None:
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

    # ------------------------------------------------------------------
    # Hotkey suppression
    # ------------------------------------------------------------------

    def _win32_event_filter(self, msg: int, data: object) -> bool:
        """Block F8 from reaching any other application on Windows.

        pynput calls this hook before the event is forwarded to the OS
        event queue.  Calling ``suppress_event()`` drops F8 entirely so
        that no other window (browser, editor, …) ever receives it.
        All other keys are passed through unchanged.
        """
        if getattr(data, "vkCode", None) == _VK_F8:
            self.listener.suppress_event()
        return True

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        self.listener.start()
        print("Ready. Hold F8 to talk; release F8 to transcribe. Press Ctrl+C to quit.")

    def stop(self) -> None:
        self.stop_recording.set()
        self.listener.stop()

    # ------------------------------------------------------------------
    # Key handlers
    # ------------------------------------------------------------------

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if key == keyboard.Key.f8 and not self.recording.is_set():
            self.recording.set()
            self.stop_recording.clear()
            threading.Thread(target=self._record, daemon=True, name="audio-recorder").start()

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if key == keyboard.Key.f8:
            self.stop_recording.set()

    # ------------------------------------------------------------------
    # Audio recording & transcription (Buffered Queue Producer-Consumer)
    # ------------------------------------------------------------------

    def _record(self) -> None:
        self.ui_events.put(("show", None))
        audio_queue: queue.Queue[np.ndarray] = queue.Queue()

        def capture(indata: np.ndarray, frames: int, time: object, status: sd.CallbackFlags) -> None:
            if status:
                print(f"Audio callback status: {status}")
            # Thread-safe queue push (fast, non-blocking for real-time audio thread safety)
            audio_queue.put(indata.copy())

        chunks: list[np.ndarray] = []
        stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=capture)

        try:
            with stream:
                # We expect sounddevice callbacks approximately every 50-100ms.
                # Stop recording when stop_recording is set or when we hit MAX_RECORDING_SECONDS.
                total_duration = 0.0
                while not self.stop_recording.is_set() and total_duration < MAX_RECORDING_SECONDS:
                    try:
                        # Pull chunks from the buffer queue with a short timeout
                        chunk = audio_queue.get(timeout=0.05)
                        chunks.append(chunk)
                        
                        # Perform heavy RMS calculation and duration updates on the worker thread
                        rms = float(np.sqrt(np.mean(np.square(chunk))))
                        self.ui_events.put(("level", min(rms * 8, 1.0)))
                        
                        # Add duration of the chunk to the accumulator
                        total_duration += len(chunk) / SAMPLE_RATE
                    except queue.Empty:
                        continue

            self.ui_events.put(("hide", None))
            if not chunks:
                return
            audio = np.concatenate(chunks, axis=0).squeeze()
            transcript = transcribe_buffer(audio, self.model)
            if transcript:
                print(f"GuideAI heard: {transcript}")
                self.on_transcript(transcript)
        except Exception as error:
            print(f"Microphone/transcription error: {error}")
        finally:
            self.ui_events.put(("hide", None))
            self.recording.clear()

    @staticmethod
    def get_raw_audio_bytes(chunks: list[np.ndarray]) -> bytes:
        """Convert float32 audio chunks into raw 16-bit PCM bytes."""
        if not chunks:
            return b""
        audio = np.concatenate(chunks, axis=0).squeeze()
        audio = np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)
        return (audio * 32767.0).astype(np.int16).tobytes()

