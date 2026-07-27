"""Fullscreen transparent click-through Qt overlay window."""

from __future__ import annotations

import sys

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QColor, QPainter
    from PyQt6.QtWidgets import QApplication, QWidget
except ImportError:
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QColor, QPainter
    from PyQt5.QtWidgets import QApplication, QWidget


class OverlayWindow(QWidget):
    """Borderless transparent overlay that ignores user input."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.showFullScreen()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        # Keep painting transparent so the overlay is visually unobtrusive.
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))


def main() -> int:
    app = QApplication(sys.argv)
    _window = OverlayWindow()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
