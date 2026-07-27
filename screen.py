"""Screen capture helpers."""

import base64
from io import BytesIO

import pyautogui

from config import (
    SCREENSHOT_JPEG_QUALITY,
    SCREENSHOT_MAX_HEIGHT,
    SCREENSHOT_MAX_WIDTH,
)


def capture_screenshot() -> str:
    """Return a compressed desktop screenshot as base64 JPEG.

    Resolution and JPEG quality are read from ``config.py`` so they can be
    tuned without touching this file:

    * ``SCREENSHOT_MAX_WIDTH`` / ``SCREENSHOT_MAX_HEIGHT`` — thumbnail ceiling.
    * ``SCREENSHOT_JPEG_QUALITY`` — JPEG quality (1–95; lower = smaller file).
    """
    image = pyautogui.screenshot()
    image.thumbnail((SCREENSHOT_MAX_WIDTH, SCREENSHOT_MAX_HEIGHT))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=SCREENSHOT_JPEG_QUALITY)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
