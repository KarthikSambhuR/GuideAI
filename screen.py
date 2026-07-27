"""Screen capture helpers."""

import base64
from io import BytesIO

from PIL import Image

try:
    import mss

    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    import pyautogui

    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False


def capture_screenshot() -> str:
    """Return a compressed desktop screenshot as base64 JPEG."""
    if HAS_MSS:
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[0]  # Full desktop bounding box
                sct_img = sct.grab(monitor)
                image = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        except Exception:
            if HAS_PYAUTOGUI:
                image = pyautogui.screenshot()
            else:
                raise RuntimeError("No working screenshot backend available (mss or pyautogui).")
    elif HAS_PYAUTOGUI:
        image = pyautogui.screenshot()
    else:
        raise RuntimeError("Neither mss nor pyautogui is installed for screen capture.")

    image.thumbnail((1280, 720))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=50)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
