"""Screen capture helpers."""

import base64
from io import BytesIO
from PIL import Image

try:
    import mss
    import mss.tools
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

from config import (
    IS_WINDOWS,
    SCREENSHOT_JPEG_QUALITY,
    SCREENSHOT_MAX_HEIGHT,
    SCREENSHOT_MAX_WIDTH,
)


def enable_dpi_awareness() -> bool:
    """Enable high-DPI awareness on Windows to prevent multi-monitor coordinate mismatch."""
    if not IS_WINDOWS:
        return False
    try:
        import ctypes
        # SetProcessDpiAwareness(2) -> PROCESS_PER_MONITOR_DPI_AWARE
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return True
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
            return True
        except Exception:
            return False


def _get_active_window_rect() -> tuple[int, int, int, int] | None:
    """Return (left, top, right, bottom) of the focused window, or None."""
    try:
        import pygetwindow as gw  # optional dependency

        win = gw.getActiveWindow()
        if win is None:
            return None
        left, top, width, height = win.left, win.top, win.width, win.height
        # Clamp to screen bounds
        screen_w, screen_h = pyautogui.size() if HAS_PYAUTOGUI else (1920, 1080)
        left = max(0, left)
        top = max(0, top)
        right = min(screen_w, left + width)
        bottom = min(screen_h, top + height)
        if right - left < 8 or bottom - top < 8:
            return None
        return left, top, right, bottom
    except Exception:
        return None


def _capture_full_screenshot():
    """Return a PIL Image of the full primary monitor.

    Uses ``mss`` for high-performance multi-monitor capture when available,
    with ``pyautogui`` as the fallback.
    """
    if HAS_MSS:
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[0]  # Full desktop bounding box
                raw = sct.grab(monitor)
                return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
        except Exception as err:
            print(f"GuideAI screen: mss capture failed ({err}), falling back to pyautogui")
    if HAS_PYAUTOGUI:
        return pyautogui.screenshot()
    raise RuntimeError("No working screenshot backend available (mss or pyautogui).")


def capture_primary_monitor():
    """Explicit helper to capture a PIL Image screenshot of the primary monitor."""
    return _capture_full_screenshot()


def capture_screenshot() -> str:
    """Return a compressed desktop screenshot as base64 JPEG.

    Attempts ``mss`` (fast, multi-monitor) first, falls back to
    ``pyautogui``.
    """
    full = _capture_full_screenshot()
    rect = _get_active_window_rect()
    if rect is not None:
        left, top, right, bottom = rect
        image = full.crop((left, top, right, bottom))
        print(f"GuideAI screen: cropped to active window {rect}")
    else:
        image = full

    image.thumbnail((SCREENSHOT_MAX_WIDTH, SCREENSHOT_MAX_HEIGHT))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=SCREENSHOT_JPEG_QUALITY)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def save_debug_image(image_b64: str, annotations: list[dict]) -> str | None:
    """Decode base64 image, draw bounding boxes/annotations, and save to local folder."""
    try:
        import os
        import time
        from PIL import ImageDraw

        img_bytes = base64.b64decode(image_b64)
        image = Image.open(BytesIO(img_bytes))
        draw = ImageDraw.Draw(image)
        width, height = image.size

        for item in annotations:
            kind = item.get("type")
            if kind == "box":
                x = float(item.get("x", 0)) * width / 1000.0
                y = float(item.get("y", 0)) * height / 1000.0
                w = float(item.get("width", 0)) * width / 1000.0
                h = float(item.get("height", 0)) * height / 1000.0
                draw.rectangle([x, y, x + w, y + h], outline="#ff3333", width=3)
                label = item.get("label")
                if label:
                    draw.text((x + 4, y + 4), str(label), fill="#ff3333")
            elif kind == "arrow":
                x1 = float(item.get("x", 0)) * width / 1000.0
                y1 = float(item.get("y", 0)) * height / 1000.0
                x2 = float(item.get("x2", 0)) * width / 1000.0
                y2 = float(item.get("y2", 0)) * height / 1000.0
                draw.line([x1, y1, x2, y2], fill="#33ffff", width=3)

        os.makedirs("debug_captures", exist_ok=True)
        filepath = os.path.join("debug_captures", f"debug_{int(time.time())}.jpg")
        image.save(filepath, format="JPEG", quality=90)
        print(f"GuideAI debug: saved annotated screenshot to {filepath}")
        return filepath
    except Exception as error:
        print(f"GuideAI debug: failed to save annotated screenshot: {error}")
        return None
