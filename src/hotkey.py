"""Global hotkey via Win32 RegisterHotKey.

No low-level keyboard hook is installed: Windows itself notifies us only
when the chosen combination is pressed. While the key is held we poll its
state (~30 ms) just to detect push-to-talk; otherwise this thread sleeps
inside GetMessageW and uses 0% CPU.
"""
import ctypes
import threading
import time
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]

MODS = {"alt": 0x1, "ctrl": 0x2, "control": 0x2, "shift": 0x4, "win": 0x8}
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012

SPECIAL_VK = {
    "space": 0x20, "pageup": 0x21, "pagedown": 0x22, "end": 0x23, "home": 0x24,
    "insert": 0x2D, "delete": 0x2E, "pause": 0x13, "scrolllock": 0x91,
    "`": 0xC0, "tab": 0x09, "capslock": 0x14,
}
for _i in range(1, 25):
    SPECIAL_VK[f"f{_i}"] = 0x70 + _i - 1
for _i in range(10):
    SPECIAL_VK[f"num{_i}"] = 0x60 + _i

VK_BY_NAME = {"alt": 0x12, "ctrl": 0x11, "shift": 0x10}


def parse_hotkey(text: str):
    parts = [p.strip().lower() for p in text.replace(" ", "").split("+") if p.strip()]
    mods, vk = 0, None
    for p in parts:
        if p in MODS:
            mods |= MODS[p]
        elif p in SPECIAL_VK:
            vk = SPECIAL_VK[p]
        elif len(p) == 1 and p.isalnum():
            vk = ord(p.upper())
        else:
            raise ValueError(f"Bilinmeyen tuş: {p}")
    if vk is None:
        raise ValueError(f"Kısayolda ana tuş yok: {text}")
    return mods, vk


def is_key_down(vk: int) -> bool:
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


class HotkeyListener(threading.Thread):
    def __init__(self, hotkey, hold_ms, on_press, on_hold, on_release, on_error):
        super().__init__(daemon=True, name="HotkeyListener")
        self.hotkey = hotkey
        self.hold_ms = hold_ms
        self.on_press, self.on_hold, self.on_release, self.on_error = on_press, on_hold, on_release, on_error
        self._tid = None

    def run(self):
        self._tid = kernel32.GetCurrentThreadId()
        try:
            mods, self.vk = parse_hotkey(self.hotkey)
        except ValueError as e:
            self.on_error(str(e))
            return
        if not user32.RegisterHotKey(None, 1, mods | MOD_NOREPEAT, self.vk):
            self.on_error(f"'{self.hotkey}' kısayolu kaydedilemedi (başka bir program kullanıyor olabilir).")
            return
        msg = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY:
                    self._handle()
        finally:
            user32.UnregisterHotKey(None, 1)

    def _handle(self):
        t0 = time.perf_counter()
        try:
            self.on_press()
        except Exception as e:  # pragma: no cover
            self.on_error(f"Hata: {e}")
            return
        held = False
        while is_key_down(self.vk):
            elapsed = time.perf_counter() - t0
            if not held and elapsed * 1000 >= self.hold_ms:
                held = True
                self.on_hold()
            if elapsed > 35:
                break
            time.sleep(0.03)
        self.on_release(held)

    def stop(self):
        if self._tid:
            user32.PostThreadMessageW(self._tid, WM_QUIT, 0, 0)
