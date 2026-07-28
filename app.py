"""Application entry point and Tk event loop."""

import queue

from pywhispercpp.model import Model

from listening_pill import ListeningPill
from llama_manager import LlamaManager
from overlay import AnnotationOverlay
from push_to_talk import PushToTalk
from question_processor import QuestionProcessor


from logger import logger


def main() -> None:
    llama = LlamaManager()
    try:
        llama.ensure_ready()
    except RuntimeError as error:
        logger.error(f"GuideAI startup error: {error}")
        return

    print("Loading the Whisper model...")
    whisper = Model("base.en", print_realtime=False, print_progress=False)
    pill = ListeningPill()
    overlay = AnnotationOverlay(pill.root)
    ui_events: queue.Queue[dict] = queue.Queue()
    questions = QuestionProcessor(ui_events.put)
    questions.start()
    voice = PushToTalk(whisper, lambda transcript, screenshot: questions.submit(transcript, screenshot))
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
        try:
            while True:
                response = ui_events.get_nowait()
                status = response.get("status")
                if status == "scanning":
                    overlay.start_scanning()
                elif status == "error":
                    overlay.stop_scanning()
                    error_msg = response.get("error", "Unknown error")
                    print(f"GuideAI processing error: {error_msg}")
                    overlay.show_error(error_msg)
                else:
                    overlay.stop_scanning()
                    overlay.show(
                        response["annotations"],
                        on_target_click=lambda target, question=response["question"]:
                            questions.continue_tutorial(question, target),
                    )
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
        questions.stop()
        overlay.stop()
        llama.stop()


if __name__ == "__main__":
    main()