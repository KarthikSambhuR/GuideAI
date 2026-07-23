"""The recording-level overlay."""

import tkinter as tk


class ListeningPill:
    """Small always-on-top overlay shown while the microphone is open."""

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
            self.root, width=self.WIDTH, height=self.HEIGHT,
            highlightthickness=0, bg=self.BACKGROUND,
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
        for index, _ in enumerate((4, 7, 11, 15, 20, 15, 11, 7, 4)):
            x = center_x - 20 + index * 5
            self.bars.append(self.canvas.create_line(
                x, self.HEIGHT // 2, x, self.HEIGHT // 2,
                fill="#ffffff", width=3, capstyle=tk.ROUND,
            ))
        self.set_level(0.0)

    def set_level(self, level: float) -> None:
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
