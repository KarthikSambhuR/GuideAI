"""Screen capture helpers."""

import base64
from io import BytesIO

import pyautogui


def capture_screenshot() -> str:
    """Return a compressed desktop screenshot as base64 JPEG."""
    image = pyautogui.screenshot()
    image.thumbnail((1280, 720))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=50)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
