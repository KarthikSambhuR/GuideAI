"""Screen capture helpers."""

import base64
from io import BytesIO

import pyautogui

from config import (
    SCREENSHOT_JPEG_QUALITY,
    SCREENSHOT_MAX_HEIGHT,
    SCREENSHOT_MAX_WIDTH,
)


def _get_active_window_rect() -> tuple[int, int, int, int] | None:
    """Return (left, top, right, bottom) of the focused window, or None."""
    try:
        import pygetwindow as gw  # optional dependency

        win = gw.getActiveWindow()
        if win is None:
            return None
        left, top, width, height = win.left, win.top, win.width, win.height
        # Clamp to screen bounds
        screen_w, screen_h = pyautogui.size()
        left = max(0, left)
        top = max(0, top)
        right = min(screen_w, left + width)
        bottom = min(screen_h, top + height)
        if right - left < 8 or bottom - top < 8:
            return None
        return left, top, right, bottom
    except Exception:
        return None


def capture_screenshot() -> str:
    """Return a compressed desktop screenshot as base64 JPEG.

    If a focused window can be detected, the screenshot is cropped to that
    window's bounds so the vision model receives a tighter, higher-detail
    view of the relevant UI. Falls back to the full desktop when the
    active window cannot be determined.

    Resolution and JPEG quality are read from ``config.py``:
    * ``SCREENSHOT_MAX_WIDTH`` / ``SCREENSHOT_MAX_HEIGHT``: thumbnail ceiling.
    * ``SCREENSHOT_JPEG_QUALITY``: JPEG quality (1–95; lower = smaller file).
    """
    full = pyautogui.screenshot()
    rect = _get_active_window_rect()
    if rect is not None:
        left, top, right, bottom = rect
        image = full.crop((left, top, right, bottom))
        print(f"GuideAI screen: cropped to active window {rect}")
    else:
        image = full
        print("GuideAI screen: capturing full desktop (no active window found)")

    image.thumbnail((SCREENSHOT_MAX_WIDTH, SCREENSHOT_MAX_HEIGHT))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=SCREENSHOT_JPEG_QUALITY)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")