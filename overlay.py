"""Screen-coordinate annotation overlay for model guidance."""

import math
import tkinter as tk
from collections.abc import Callable, Iterable

from pynput import mouse

from config import OVERLAY_DURATION_MS


class AnnotationOverlay:
    """Draw non-interactive-looking boxes, arrows, and labels over the desktop."""

    TRANSPARENT = "#ff00ff"
    COLOR = "#24d6ff"

    def __init__(self, parent: tk.Tk) -> None:
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-transparentcolor", self.TRANSPARENT)
        self.window.configure(bg=self.TRANSPARENT)
        self.width = parent.winfo_screenwidth()
        self.height = parent.winfo_screenheight()
        self.window.geometry(f"{self.width}x{self.height}+0+0")
        self.canvas = tk.Canvas(
            self.window, width=self.width, height=self.height,
            highlightthickness=0, bg=self.TRANSPARENT,
        )
        self.canvas.pack()
        self._hide_after: str | None = None
        self._on_target_click: Callable[[dict], None] | None = None
        self._target: tuple[float, float, float, float, dict] | None = None
        self._mouse_listener = mouse.Listener(on_click=self._on_click)
        self._mouse_listener.start()
        self._enable_click_through()

    def show(self, annotations: Iterable[dict], on_target_click: Callable[[dict], None] | None = None) -> None:
        """Render normalized (0-1000) model coordinates on the actual screen."""
        self.width = self.window.winfo_screenwidth()
        self.height = self.window.winfo_screenheight()
        self.window.geometry(f"{self.width}x{self.height}+0+0")
        self.canvas.configure(width=self.width, height=self.height)
        self.canvas.delete("all")
        self._target = None
        self._on_target_click = on_target_click
        items = list(annotations)
        print(f"GuideAI overlay: rendering {len(items)} annotations")
        for annotation in items:
            kind = annotation.get("type")
            if kind == "box":
                self._draw_box(annotation)
            elif kind == "arrow":
                self._draw_arrow(annotation)
            elif kind == "text":
                self._draw_text(annotation)
        if not self.canvas.find_all():
            return
        self.window.deiconify()
        self.window.lift()
        self._enable_click_through()
        if self._hide_after:
            self.window.after_cancel(self._hide_after)
        self._hide_after = self.window.after(OVERLAY_DURATION_MS, self.hide)

    def hide(self) -> None:
        self.window.withdraw()
        self._hide_after = None

    def stop(self) -> None:
        self._mouse_listener.stop()

    def _point(self, x: object, y: object) -> tuple[float, float]:
        return self._number(x) * self.width / 1000, self._number(y) * self.height / 1000

    @staticmethod
    def _number(value: object) -> float:
        try:
            return max(0.0, min(1000.0, float(value)))
        except (TypeError, ValueError):
            return 0.0

    def _draw_box(self, item: dict) -> None:
        x, y = self._point(item.get("x"), item.get("y"))
        width = self._number(item.get("width")) * self.width / 1000
        height = self._number(item.get("height")) * self.height / 1000
        if width < 4 or height < 4:
            return
        width = min(width, self.width - x)
        height = min(height, self.height - y)
        if width < 4 or height < 4:
            return
        self.canvas.create_rectangle(x, y, x + width, y + height, outline=self.COLOR, width=4)
        self._label(x, y, str(item.get("label", "")))
        if self._target is None:
            self._target = (x, y, x + width, y + height, dict(item))

    def _draw_arrow(self, item: dict) -> None:
        x1, y1 = self._point(item.get("x"), item.get("y"))
        x2, y2 = self._point(item.get("x2"), item.get("y2"))
        if math.hypot(x2 - x1, y2 - y1) < 8:
            return
        self.canvas.create_line(x1, y1, x2, y2, fill=self.COLOR, width=5, arrow=tk.LAST, arrowshape=(16, 20, 7))
        self._label(x2, y2, str(item.get("label", "")))

    def _draw_text(self, item: dict) -> None:
        x, y = self._point(item.get("x"), item.get("y"))
        self._caption(x, y, str(item.get("text", "")))

    def _caption(self, x: float, y: float, text: str) -> None:
        """Draw a high-contrast tutorial card that remains visible on any desktop."""
        if not text:
            return
        left = min(max(8, x), max(8, self.width - 440))
        top = min(max(8, y), max(8, self.height - 100))
        right = min(self.width - 8, left + 430)
        bottom = min(self.height - 8, top + 86)
        self.canvas.create_rectangle(left, top, right, bottom, fill="#102a43", outline=self.COLOR, width=2)
        self.canvas.create_text(
            left + 12, top + 10, text=text, anchor=tk.NW, fill="white",
            font=("Segoe UI", 12, "bold"), justify=tk.LEFT, width=400,
        )

    def _label(self, x: float, y: float, label: str) -> None:
        if not label:
            return
        label_x = min(max(8, x + 8), max(8, self.width - 360))
        label_y = min(max(20, y - 8), self.height - 8)
        self.canvas.create_text(
            label_x, label_y, text=label, anchor=tk.SW, fill="white",
            font=("Segoe UI", 12, "bold"),
            justify=tk.LEFT, width=360,
        )

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if not pressed or button != mouse.Button.left or self._target is None:
            return
        left, top, right, bottom, target = self._target
        if left <= x <= right and top <= y <= bottom:
            self._target = None
            if self._on_target_click:
                self._on_target_click(target)

    def _enable_click_through(self) -> None:
        """Keep the overlay from blocking the actual desktop interface."""
        try:
            import ctypes

            hwnd = self.window.winfo_id()
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x20 | 0x80000)
        except (AttributeError, OSError):
            pass
