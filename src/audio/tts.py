"""Text-to-Speech (TTS) announcement engine for GuideAI."""

import queue
import threading

from config import ENABLE_TTS


class TTSManager:
    """Non-blocking Text-to-Speech speech engine using pyttsx3 or SAPI5."""

    def __init__(self) -> None:
        self.enabled = ENABLE_TTS
        self.speech_queue: queue.Queue[str | None] = queue.Queue()
        self.engine = None
        self.worker = threading.Thread(target=self._run, daemon=True, name="tts-speech-worker")
        if self.enabled:
            self.worker.start()

    def speak(self, text: str) -> None:
        """Queue text to be spoken out loud asynchronously."""
        if not self.enabled or not text:
            return
        self.speech_queue.put(text)

    def stop(self) -> None:
        if self.enabled:
            self.speech_queue.put(None)

    def _run(self) -> None:
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 175)
        except Exception:
            self.engine = None

        while True:
            text = self.speech_queue.get()
            if text is None:
                break
            if self.engine:
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as err:
                    print(f"GuideAI TTS error: {err}")
            self.speech_queue.task_done()
