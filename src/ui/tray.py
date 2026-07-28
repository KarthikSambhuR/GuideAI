"""Background system tray icon manager for GuideAI."""

import threading
from collections.abc import Callable


class TrayManager:
    """System tray icon manager allowing quick background status control."""

    def __init__(self, on_exit: Callable[[], None] | None = None) -> None:
        self.on_exit = on_exit
        self.icon = None
        self.thread = None

    def start(self) -> None:
        """Start the system tray icon runner in a background daemon thread."""
        self.thread = threading.Thread(target=self._run_tray, daemon=True, name="system-tray-worker")
        self.thread.start()

    def stop(self) -> None:
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass

    def _run_tray(self) -> None:
        try:
            import pystray
            from PIL import Image, ImageDraw

            # Create a simple icon programmatically
            image = Image.new("RGBA", (64, 64), (13, 31, 45, 255))
            draw = ImageDraw.Draw(image)
            draw.ellipse((8, 8, 56, 56), outline="#24d6ff", width=4)
            draw.text((24, 20), "AI", fill="#ffffff")

            menu = pystray.Menu(
                pystray.MenuItem("GuideAI Active", lambda: None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", self._handle_exit),
            )

            self.icon = pystray.Icon("GuideAI", image, "GuideAI Desktop Assistant", menu)
            self.icon.run()
        except Exception as err:
            print(f"GuideAI tray icon note: pystray tray icon not active ({err})")

    def _handle_exit(self) -> None:
        self.stop()
        if self.on_exit:
            self.on_exit()
