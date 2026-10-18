"""100% in-memory screen capture. Nothing is ever written to disk.

Uses the OS screen-duplication path (same as OBS / Discord screen share).
The game process is never touched: no memory reads, no injection, no hooks.
"""
import io

import mss
from PIL import Image


def _grab_mss(monitor_index: int) -> Image.Image:
    with mss.mss() as sct:
        monitors = sct.monitors
        idx = monitor_index if 0 < monitor_index < len(monitors) else 1
        shot = sct.grab(monitors[idx])
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        del shot
    return img


def _grab_pil() -> Image.Image:
    from PIL import ImageGrab
    return ImageGrab.grab().convert("RGB")


def grab_screen_jpeg(monitor_index: int = 1, max_width: int = 1920, quality: int = 85) -> bytes:
    try:
        img = _grab_mss(monitor_index)
    except Exception:
        img = _grab_pil()  # fallback (primary screen); still RAM-only

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
