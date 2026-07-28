"""The recording-level overlay."""

import tkinter as tk

from config import IS_WINDOWS, UI_FONT_FAMILY


class ListeningPill:
    """Small always-on-top overlay shown while recording or processing."""

    WIDTH = 130
    HEIGHT = 46
    BACKGROUND = "#ff00ff" if IS_WINDOWS else "#1e1e2e"

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        if IS_WINDOWS:
            self.root.attributes("-transparentcolor", self.BACKGROUND)
        else:
            try:
                self.root.attributes("-alpha", 0.9)
            except tk.TclError:
                pass
        self.root.configure(bg=self.BACKGROUND)

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - self.WIDTH) // 2
        y = screen_height - self.HEIGHT - 105
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        self.canvas = tk.Canvas(
            self.root, width=self.WIDTH, height=self.HEIGHT,
            highlightthickness=0, bg=self.BACKGROUND,
        )
        self.canvas.pack()
        self.current_level = 0.0
        self.mode = "recording"
        self._thinking_after: str | None = None
        self._thinking_step = 0
        self._draw_pill()

    def _draw_pill(self) -> None:
        radius, fill = 23, "#000000"
        self.canvas.create_rectangle(radius, 0, self.WIDTH - radius, self.HEIGHT, fill=fill, outline=fill)
        self.canvas.create_oval(0, 0, radius * 2, self.HEIGHT, fill=fill, outline=fill)
        self.canvas.create_oval(self.WIDTH - radius * 2, 0, self.WIDTH, self.HEIGHT, fill=fill, outline=fill)

        self.bars: list[int] = []
        center_x = self.WIDTH // 2
        for index, _ in enumerate((4, 7, 11, 15, 20, 15, 11, 7, 4)):
            x = center_x - 20 + index * 5
            self.bars.append(self.canvas.create_line(
                x, self.HEIGHT // 2, x, self.HEIGHT // 2,
                fill="#ffffff", width=3, capstyle=tk.ROUND,
            ))
        self.text_item = self.canvas.create_text(
            self.WIDTH // 2, self.HEIGHT // 2,
            text="Thinking...", fill="#24d6ff",
            font=(UI_FONT_FAMILY, 10, "bold"),
            state=tk.HIDDEN,
        )
        self.set_level(0.0)

    def set_level(self, level: float) -> None:
        if self.mode != "recording":
            return
        target_level = min(max(level, 0.0), 1.0)
        # Exponential Moving Average (EMA) smoothing: α=0.35 for fluid bar movement.
        # Formula: level_t = α * new_level + (1 - α) * level_{t-1}
        self.current_level = 0.35 * target_level + 0.65 * self.current_level
        base_heights = (4, 7, 11, 15, 20, 15, 11, 7, 4)
        center_y = self.HEIGHT // 2
        for bar, base_height in zip(self.bars, base_heights):
            height = max(3, base_height * (0.28 + self.current_level * 0.72))
            x = self.canvas.coords(bar)[0]
            self.canvas.coords(bar, x, center_y - height / 2, x, center_y + height / 2)

    def show(self) -> None:
        self.mode = "recording"
        self._cancel_thinking()
        for bar in self.bars:
            self.canvas.itemconfig(bar, state=tk.NORMAL)
        self.canvas.itemconfig(self.text_item, state=tk.HIDDEN)
        self.root.deiconify()
        self.root.lift()

    def show_thinking(self) -> None:
        """Switch the pill to an animated 'Thinking…' state."""
        self.mode = "thinking"
        for bar in self.bars:
            self.canvas.itemconfig(bar, state=tk.HIDDEN)
        self.canvas.itemconfig(self.text_item, state=tk.NORMAL)
        self.root.deiconify()
        self.root.lift()
        self._animate_thinking()

    def _animate_thinking(self) -> None:
        if self.mode != "thinking":
            return
        dots = "." * ((self._thinking_step % 4) + 1)
        self.canvas.itemconfig(self.text_item, text=f"Thinking{dots}")
        self._thinking_step += 1
        self._thinking_after = self.root.after(300, self._animate_thinking)

    def _cancel_thinking(self) -> None:
        if self._thinking_after:
            self.root.after_cancel(self._thinking_after)
            self._thinking_after = None

    def hide(self) -> None:
        self.mode = "hidden"
        self._cancel_thinking()
        self.root.withdraw()
