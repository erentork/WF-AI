"""100% in-memory screen capture. Nothing is ever written to disk.

Uses the OS screen-duplication path (same as OBS / Discord screen share).
The game process is never touched: no memory reads, no injection, no hooks.
"""
import io

import mss
from PIL import Image


import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)


def _find_active_monitor(monitors: list) -> int:
    """Returns the mss monitor index (1..N) containing the foreground window or cursor."""
    if len(monitors) <= 2:
        return 1
    rect = wintypes.RECT()
    hwnd = user32.GetForegroundWindow()
    if hwnd and user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        cx = (rect.left + rect.right) // 2
        cy = (rect.top + rect.bottom) // 2
    else:
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        cx, cy = pt.x, pt.y

    for i in range(1, len(monitors)):
        m = monitors[i]
        if m["left"] <= cx < m["left"] + m["width"] and m["top"] <= cy < m["top"] + m["height"]:
            return i
    return 1


def _grab_mss(monitor_index: int) -> Image.Image:
    with mss.mss() as sct:
        monitors = sct.monitors
        if monitor_index == 0:
            idx = _find_active_monitor(monitors)
        else:
            idx = monitor_index if 0 < monitor_index < len(monitors) else _find_active_monitor(monitors)
        shot = sct.grab(monitors[idx])
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        del shot
    return img


def _grab_pil(monitor_index: int = 0) -> Image.Image:
    from PIL import ImageGrab
    with mss.mss() as sct:
        monitors = sct.monitors
        idx = _find_active_monitor(monitors) if monitor_index == 0 else (
            monitor_index if 0 < monitor_index < len(monitors) else 1
        )
        m = monitors[idx]
        bbox = (m["left"], m["top"], m["left"] + m["width"], m["top"] + m["height"])
    return ImageGrab.grab(bbox=bbox, all_screens=True).convert("RGB")


def grab_screen_jpeg(monitor_index: int = 0, max_width: int = 1920, quality: int = 85) -> bytes:
    try:
        img = _grab_mss(monitor_index)
    except Exception:
        img = _grab_pil(monitor_index)  # fallback (multi-monitor aware); still RAM-only

    if img.width > max_width:
        new_h = round(img.height * max_width / img.width)
        resized = img.resize((max_width, new_h), Image.Resampling.LANCZOS)
        img.close()
        img = resized

    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality)
    img.close()
    data = buf.getvalue()
    buf.close()
    return data
