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

    def show_error(self, message: str) -> None:
        """Render a visually distinct error banner in the center of the screen."""
        self.width = self.window.winfo_screenwidth()
        self.height = self.window.winfo_screenheight()
        self.window.geometry(f"{self.width}x{self.height}+0+0")
        self.canvas.configure(width=self.width, height=self.height)
        self.canvas.delete("all")
        self._target = None

        cx, cy = self.width // 2, self.height // 2
        w, h = 480, 110
        left = cx - w // 2
        top = cy - h // 2
        right = left + w
        mid = top + 28
        bottom = top + h

        # Red themed error card
        self.canvas.create_rectangle(left, top, right, bottom, fill="#1c0d0d", outline="#ff4a4a", width=2)
        self.canvas.create_rectangle(left + 2, top + 2, right - 2, mid, fill="#b51a1a", outline="")
        self.canvas.create_text(
            left + 12, top + 14, text="⚠️ GuideAI Error", anchor=tk.W, fill="white", font=("Segoe UI", 10, "bold")
        )
        self.canvas.create_line(left + 2, mid, right - 2, mid, fill="#ff4a4a", width=1)
        self.canvas.create_text(
            left + 12, mid + 8, text=message, anchor=tk.NW, fill="#ffd2d2",
            font=("Segoe UI", 11, "bold"), justify=tk.LEFT, width=w - 24
        )
        self.canvas.create_text(
            right - 12, bottom - 8, text="will auto-dismiss in 6s", anchor=tk.SE, fill="#d68484", font=("Segoe UI", 8)
        )

        self.window.deiconify()
        self.window.lift()
        self._enable_click_through()

        if self._hide_after:
            self.window.after_cancel(self._hide_after)
        self._hide_after = self.window.after(6000, self.hide)

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

    # Banner geometry constants
    _BANNER_W = 480
    _HEADER_H = 28
    _BODY_H = 90
    _BANNER_H = _HEADER_H + _BODY_H
    _PAD = 12

    def _caption(self, x: float, y: float, text: str) -> None:
        """Draw a branded instruction banner with a header strip and body text.

        Layout
        ------
        ┌─────────────────────────────────────────┐  ← cyan header (28 px)
        │  ✦ GuideAI                              │
        ├─────────────────────────────────────────┤
        │  <step text, word-wrapped>              │  ← dark body  (90 px)
        │                   click target to cont →│
        └─────────────────────────────────────────┘
        """
        if not text:
            return

        w, h = self._BANNER_W, self._BANNER_H
        # Pin the banner so it never goes off-screen.
        left = int(min(max(self._PAD, x), self.width - w - self._PAD))
        top = int(min(max(self._PAD, y), self.height - h - self._PAD))
        right = left + w
        mid = top + self._HEADER_H
        bottom = top + h

        # ── outer border ────────────────────────────────────────────────
        self.canvas.create_rectangle(
            left, top, right, bottom,
            fill="#0d1f2d", outline=self.COLOR, width=2,
        )

        # ── cyan header strip ────────────────────────────────────────────
        self.canvas.create_rectangle(
            left + 2, top + 2, right - 2, mid,
            fill="#0a9dba", outline="",
        )
        self.canvas.create_text(
            left + self._PAD, top + self._HEADER_H // 2,
            text="✦ GuideAI",
            anchor=tk.W, fill="#ffffff",
            font=("Segoe UI", 10, "bold"),
        )

        # ── separator line ───────────────────────────────────────────────
        self.canvas.create_line(
            left + 2, mid, right - 2, mid,
            fill=self.COLOR, width=1,
        )

        # ── step text ────────────────────────────────────────────────────
        self.canvas.create_text(
            left + self._PAD, mid + 8,
            text=text,
            anchor=tk.NW, fill="#e8f4f8",
            font=("Segoe UI", 11, "bold"),
            justify=tk.LEFT,
            width=w - self._PAD * 2,
        )

        # ── hint line ────────────────────────────────────────────────────
        self.canvas.create_text(
            right - self._PAD, bottom - 8,
            text="click the highlighted target to continue →",
            anchor=tk.SE, fill="#5ba3b8",
            font=("Segoe UI", 8),
        )

    def _label(self, x: float, y: float, label: str) -> None:
        """Draw a label with a dark pill background so it reads on any wallpaper."""
        if not label:
            return
        lx = min(max(8, x + 8), max(8, self.width - 360))
        ly = min(max(20, y - 8), self.height - 8)
        # Measure approximate text bbox and draw a backing rectangle first.
        char_w, char_h = 7, 15
        tw = min(len(label) * char_w, 350)
        th = char_h
        pad = 4
        self.canvas.create_rectangle(
            lx - pad, ly - th - pad,
            lx + tw + pad, ly + pad,
            fill="#0d1f2d", outline=self.COLOR, width=1,
        )
        self.canvas.create_text(
            lx, ly, text=label, anchor=tk.SW, fill="#e8f4f8",
            font=("Segoe UI", 11, "bold"),
            justify=tk.LEFT, width=350,
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
