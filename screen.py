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


def save_debug_image(image_b64: str, annotations: list[dict]) -> str | None:
    """Decode base64 image, draw bounding boxes/annotations, and save to local folder.

    Saves annotated screenshots to ``debug_captures/``, which is useful for
    developers verifying VLM detection alignment and cropped scale.
    """
    try:
        import os
        import time
        from PIL import Image, ImageDraw

        img_bytes = base64.b64decode(image_b64)
        image = Image.open(BytesIO(img_bytes))
        draw = ImageDraw.Draw(image)
        width, height = image.size

        for item in annotations:
            kind = item.get("type")
            if kind == "box":
                # Convert normalized VLM coordinates (0-1000) to actual pixels
                x = float(item.get("x", 0)) * width / 1000.0
                y = float(item.get("y", 0)) * height / 1000.0
                w = float(item.get("width", 0)) * width / 1000.0
                h = float(item.get("height", 0)) * height / 1000.0
                
                # Draw a bright red rectangle
                draw.rectangle([x, y, x + w, y + h], outline="#ff3333", width=3)
                
                label = item.get("label")
                if label:
                    draw.text((x + 4, y + 4), str(label), fill="#ff3333")
            elif kind == "arrow":
                x1 = float(item.get("x", 0)) * width / 1000.0
                y1 = float(item.get("y", 0)) * height / 1000.0
                x2 = float(item.get("x2", 0)) * width / 1000.0
                y2 = float(item.get("y2", 0)) * height / 1000.0
                
                # Draw a bright cyan line
                draw.line([x1, y1, x2, y2], fill="#33ffff", width=3)

        # Create output directory inside workspace
        os.makedirs("debug_captures", exist_ok=True)
        filepath = os.path.join("debug_captures", f"debug_{int(time.time())}.jpg")
        image.save(filepath, format="JPEG", quality=90)
        print(f"GuideAI debug: saved annotated screenshot to {filepath}")
        return filepath
    except Exception as error:
        print(f"GuideAI debug: failed to save annotated screenshot: {error}")
        return None