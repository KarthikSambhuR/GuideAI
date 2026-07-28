"""Fullscreen transparent click-through Qt overlay window.

This module provides a lightweight fullscreen Qt window that is fully
transparent and ignores all mouse/keyboard input, making it suitable
as a base layer for rendering GuideAI annotations without interfering
with the user's desktop.

Usage::

    python -m src.ui.overlay

Or import and instantiate ``OverlayWindow`` in your own Qt application.
"""

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
    """Borderless transparent overlay that ignores user input.

    The window is always on top, fully transparent to mouse events, and
    renders nothing but a transparent background.  Sub-class this and
    override ``paintEvent`` to draw custom guidance annotations.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.showFullScreen()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        # Keep painting transparent so the overlay is visually unobtrusive.
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))


def main() -> int:
    """Launch a standalone transparent overlay window for testing."""
    app = QApplication(sys.argv)
    _window = OverlayWindow()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
