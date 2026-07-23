"""Application entry point and Tk event loop."""

import queue

from pywhispercpp.model import Model

from listening_pill import ListeningPill
from push_to_talk import PushToTalk
from question_processor import QuestionProcessor


def main() -> None:
    print("Loading the Whisper model...")
    whisper = Model("base.en", print_realtime=False, print_progress=False)
    print("Starting the GuideAI vision worker...")
    questions = QuestionProcessor()
    questions.start()
    pill = ListeningPill()
    voice = PushToTalk(whisper, questions.submit)
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
        questions.stop()


if __name__ == "__main__":
    main()
