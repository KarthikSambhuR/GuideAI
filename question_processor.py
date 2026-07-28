"""Non-blocking Gemma 4 E2B vision requests and annotation parsing."""

import json
import queue
import re
import threading
from collections.abc import Callable
from urllib.request import Request, urlopen

from config import LLAMA_MODEL, LLAMA_REQUEST_TIMEOUT_SECONDS, LLAMA_SERVER_URL
from screen import capture_screenshot


ANNOTATION_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "annotations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["box", "arrow", "text"]},
                    "x": {"type": "number", "minimum": 0, "maximum": 1000},
                    "y": {"type": "number", "minimum": 0, "maximum": 1000},
                    "width": {"type": "number", "minimum": 0, "maximum": 1000},
                    "height": {"type": "number", "minimum": 0, "maximum": 1000},
                    "x2": {"type": "number", "minimum": 0, "maximum": 1000},
                    "y2": {"type": "number", "minimum": 0, "maximum": 1000},
                    "label": {"type": "string"},
                    "text": {"type": "string"},
                },
                "required": ["type", "x", "y"],
            },
        },
    },
    "required": ["answer", "annotations"],
}

PROMPT = """You are GuideAI, a visual guide for the current desktop screenshot.
Answer the user's request as a short, practical tutorial and identify the next exact
visible interface element they should click. Return only the requested JSON object.
Coordinates are normalized to 0-1000 over the full screenshot: x grows left-to-right
and y grows top-to-bottom. Return exactly one box around the next click target and one
arrow pointing to it. Use a short label such as \"1. Click Settings\". Never invent a
location that is not visibly supported by the screenshot."""


def get_system_prompt(custom_context: str = "") -> str:
    """Formulate the complete system prompt for guide instructions."""
    if custom_context:
        return f"{PROMPT}\n\nAdditional Context: {custom_context}"
    return PROMPT



class QuestionProcessor:
    """Queue questions so model work never blocks microphone input."""

    def __init__(self, on_response: Callable[[dict], None]) -> None:
        self.on_response = on_response
        self.questions: queue.Queue[tuple[str, dict | None] | None] = queue.Queue()
        self._history: list[dict] = []
        self.worker = threading.Thread(target=self._run, daemon=True, name="vision-request-worker")

    def start(self) -> None:
        self.worker.start()

    def submit(self, question: str) -> None:
        self._history = []
        self.questions.put((question, None))
        print("GuideAI: question queued.")

    def continue_tutorial(self, question: str, completed_target: dict) -> None:
        """Capture the updated screen and ask the model for the next click."""
        self._history.append(completed_target)
        self.questions.put((question, completed_target))
        print(f"GuideAI: click detected (completed: {completed_target.get('label', 'unlabeled')}); finding the next step...")

    def stop(self) -> None:
        self.questions.put(None)

    def _run(self) -> None:
        while True:
            task = self.questions.get()
            if task is None:
                return
            question, completed_target = task
            try:
                self.on_response({"status": "scanning"})
                response = self._ask_model(question, completed_target)
                print(f"GuideAI: {response['answer']}\n")
                response["status"] = "done"
                self.on_response(response)
            except Exception as error:
                print(f"GuideAI request error: {error}")
                self.on_response({"status": "error", "error": str(error)})
            finally:
                self.questions.task_done()

    def _parse_llm_json(self, raw: str) -> dict:
        """Robustly parse a JSON object from the model's raw text output.

        The model may wrap its JSON in markdown code fences or include
        trailing prose.  This method tries three strategies in order:

        1. Plain ``json.loads`` on the full string (fast path, covers
           well-behaved responses).
        2. Strip markdown code fences (`` ```json … ``` `` or `` ``` … `` ``)
           then parse again.
        3. Use a regex to extract the first ``{ … }`` block and parse that.

        Raises ``ValueError`` if all strategies fail.
        """
        text = raw.strip()

        # Strategy 1 — plain parse.
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strategy 2 — strip markdown fences.
        fence_re = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
        match = fence_re.search(text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Strategy 3 — extract first {...} block.
        brace_re = re.compile(r"(\{.*\})", re.DOTALL)
        match = brace_re.search(text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        raise ValueError(
            f"Could not parse JSON from model output. "
            f"First 200 chars: {text[:200]!r}"
        )

    def _ask_model(self, question: str, completed_target: dict | None = None) -> dict:
        screenshot = capture_screenshot()
        continuation = ""
        if self._history:
            steps_summary = []
            for idx, target in enumerate(self._history):
                label = target.get("label") or f"target at ({target.get('x')}, {target.get('y')})"
                steps_summary.append(f"Step {idx + 1}: Clicked '{label}'")
            steps_text = "\n".join(steps_summary)
            continuation = (
                f"\n\nHere is the history of steps the user has already completed in this tutorial:\n"
                f"{steps_text}\n\n"
                f"Use the new screenshot to determine the NEXT click. Do not repeat or re-highlight "
                f"any of the completed steps above."
            )
        body = {
            "model": LLAMA_MODEL,
            "stream": False,
            "temperature": 0,
            "response_format": {"type": "json_object", "schema": ANNOTATION_SCHEMA},
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{PROMPT}\n\nUser request: {question}{continuation}"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{screenshot}"},
                    },
                ],
            }],
        }
        request = Request(
            LLAMA_SERVER_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=LLAMA_REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.load(response)
        raw_content = payload["choices"][0]["message"]["content"]
        result = self._parse_llm_json(raw_content)
        if not isinstance(result.get("answer"), str) or not isinstance(result.get("annotations"), list):
            raise ValueError("Gemma returned an invalid guidance response.")
        result["annotations"] = [
            item for item in result["annotations"]
            if isinstance(item, dict) and item.get("type") in {"box", "arrow", "text"}
        ]
        print(f"GuideAI: model returned {len(result['annotations'])} visual annotations.")
        # Always display the model's spoken guidance as a visible tutorial caption,
        # even if the model omits an optional text annotation of its own.
        result["annotations"].append({
            "type": "text",
            "x": 24,
            "y": 40,
            "text": result["answer"],
        })
        result["question"] = question

        # Save an annotated copy locally for developer verification (Issue #16)
        try:
            from screen import save_debug_image
            save_debug_image(screenshot, result["annotations"])
        except Exception as err:
            print(f"GuideAI debug: failed to save step image: {err}")

        return result
