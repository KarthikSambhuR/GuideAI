"""GuideAI push-to-talk client.

Hold F8 to record a command.  The listening pill is shown for the whole time
the microphone is open and the transcript is printed when F8 is released.
"""

import queue
import threading
import base64
from collections.abc import Callable
from io import BytesIO

import numpy as np
import pyautogui
import sounddevice as sd
import tkinter as tk
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pynput import keyboard
from pywhispercpp.model import Model


SAMPLE_RATE = 16_000
MAX_RECORDING_SECONDS = 60


class ListeningPill:
    """Small click-through-looking overlay modelled after the supplied clip."""

    WIDTH = 122
    HEIGHT = 46
    BACKGROUND = "#ff00ff"  # Windows transparent-colour key.

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", self.BACKGROUND)
        self.root.configure(bg=self.BACKGROUND)

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - self.WIDTH) // 2
        y = screen_height - self.HEIGHT - 105
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        self.canvas = tk.Canvas(
            self.root,
            width=self.WIDTH,
            height=self.HEIGHT,
            highlightthickness=0,
            bg=self.BACKGROUND,
        )
        self.canvas.pack()
        self._draw_pill()

    def _draw_pill(self) -> None:
        radius, fill = 23, "#000000"
        self.canvas.create_rectangle(radius, 0, self.WIDTH - radius, self.HEIGHT, fill=fill, outline=fill)
        self.canvas.create_oval(0, 0, radius * 2, self.HEIGHT, fill=fill, outline=fill)
        self.canvas.create_oval(self.WIDTH - radius * 2, 0, self.WIDTH, self.HEIGHT, fill=fill, outline=fill)

        self.bars: list[int] = []
        center_x = self.WIDTH // 2
        for index, base_height in enumerate((4, 7, 11, 15, 20, 15, 11, 7, 4)):
            x = center_x - 20 + index * 5
            bar = self.canvas.create_line(x, self.HEIGHT // 2, x, self.HEIGHT // 2, fill="#ffffff", width=3, capstyle=tk.ROUND)
            self.bars.append(bar)
        self.set_level(0.0)

    def set_level(self, level: float) -> None:
        """Update the equalizer; level is a normalized microphone amplitude."""
        level = min(max(level, 0.0), 1.0)
        base_heights = (4, 7, 11, 15, 20, 15, 11, 7, 4)
        center_y = self.HEIGHT // 2
        for bar, base_height in zip(self.bars, base_heights):
            height = max(3, base_height * (0.28 + level * 0.72))
            x = self.canvas.coords(bar)[0]
            self.canvas.coords(bar, x, center_y - height / 2, x, center_y + height / 2)

    def show(self) -> None:
        self.root.deiconify()
        self.root.lift()

    def hide(self) -> None:
        self.root.withdraw()


class PushToTalk:
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
            threading.Thread(target=self._record, daemon=True).start()

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
            # Listening has ended as soon as the microphone stream closes.  Keep
            # the (potentially slower) transcription work out of the UI state.
            self.ui_events.put(("hide", None))
            if chunks:
                audio = np.concatenate(chunks, axis=0).squeeze()
                audio = np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)
                peak = np.max(np.abs(audio))
                if peak:
                    audio /= peak
                transcript = " ".join(segment.text for segment in self.model.transcribe(audio)).strip()
                if transcript:
                    self.on_transcript(transcript)
        except Exception as error:
            print(f"Microphone error: {error}")
        finally:
            self.ui_events.put(("hide", None))
            self.recording.clear()


def screenshot() -> str:
    """Capture a modest-sized screenshot for the vision model."""
    image = pyautogui.screenshot()
    image.thumbnail((1280, 720))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=50)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def answer_question(agent: object, question: str) -> None:
    """Send the spoken command and current screen to the existing vision agent."""
    print(f"GuideAI heard: {question}")
    try:
        image = screenshot()
        message = HumanMessage(
            content=[
                {"type": "text", "text": f"Look at this screenshot. The user asked: {question}. Describe what you see that matches their request."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}},
            ]
        )
        result = agent.invoke({"messages": [message]})
        print(f"GuideAI: {result['messages'][-1].content}\n")
    except Exception as error:
        print(f"GuideAI error: {error}")


def main() -> None:
    print("Loading the Whisper model...")
    model = Model("base.en", print_realtime=False, print_progress=False)
    print("Connecting to the vision model...")
    vlm = ChatOpenAI(
        model="moondream",
        api_key="ollama",
        base_url="http://localhost:11434/v1",
        temperature=0.0,
    )
    agent = create_agent(vlm, [])
    pill = ListeningPill()
    voice = PushToTalk(model, lambda text: answer_question(agent, text))
    voice.start()

    def process_ui_events() -> None:
        try:
            while True:
                action, value = voice.ui_events.get_nowait()
                if action == "show":
                    pill.show()
                elif action == "hide":
                    pill.hide()
                elif action == "level" and value is not None:
                    pill.set_level(value)
        except queue.Empty:
            pass
        pill.root.after(33, process_ui_events)

    process_ui_events()
    try:
        pill.root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        voice.stop()


if __name__ == "__main__":
    main()
