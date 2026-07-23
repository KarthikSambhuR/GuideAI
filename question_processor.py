"""Non-blocking, serialized requests to the local vision model."""

import queue
import threading

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from config import OLLAMA_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL
from screen import capture_screenshot


class QuestionProcessor:
    """Queue questions so network errors never block recording or F8."""

    def __init__(self) -> None:
        self.questions: queue.Queue[str | None] = queue.Queue()
        self.model = ChatOpenAI(
            model=OLLAMA_MODEL,
            api_key=OLLAMA_API_KEY,
            base_url=OLLAMA_BASE_URL,
            temperature=0.0,
            timeout=30,
            max_retries=1,
        )
        self.worker = threading.Thread(target=self._run, daemon=True, name="vision-request-worker")

    def start(self) -> None:
        self.worker.start()

    def submit(self, question: str) -> None:
        self.questions.put(question)
        print("GuideAI: question queued.")

    def stop(self) -> None:
        self.questions.put(None)

    def _run(self) -> None:
        while True:
            question = self.questions.get()
            if question is None:
                return
            try:
                image = capture_screenshot()
                message = HumanMessage(content=[
                    {"type": "text", "text": (
                        "Look at this screenshot. The user asked: "
                        f"{question}. Describe what you see that matches their request."
                    )},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}},
                ])
                result = self.model.invoke([message])
                print(f"GuideAI: {result.content}\n")
            except Exception as error:
                print(f"GuideAI connection error: {error}")
            finally:
                self.questions.task_done()
