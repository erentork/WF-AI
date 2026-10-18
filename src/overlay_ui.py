"""Shape-shifting pet overlay (PyQt6, custom QPainter drawing).

idle / scan / listen -> minimalist Cyber-HUD pill (design 3)
riven                -> purple Cephalon crystal (design 1)
build                -> blue Cephalon crystal   (design 1)
relic                -> golden Orokin Void eye  (design 2)

Performance: in idle the animation timer is stopped (0% CPU / GPU).
The window is click-through; hold the interact key (Alt) to click/drag it.
"""
import ctypes
import math

from PyQt6.QtCore import QPoint, QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen,
                         QRadialGradient)
from PyQt6.QtWidgets import QApplication, QLabel, QLayout, QVBoxLayout, QWidget

user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.GetWindowLongW.restype = ctypes.c_long
user32.SetWindowLongW.restype = ctypes.c_long

GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_LAYERED = 0x00080000
WS_EX_NOACTIVATE = 0x08000000
INTERACT_VK = {"alt": 0x12, "ctrl": 0x11, "shift": 0x10}

THEME = {
    "idle": QColor(16, 185, 129),
    "scan": QColor(16, 185, 129),
    "listen": QColor(52, 211, 153),
    "world": QColor(16, 185, 129),
    "riven": QColor(168, 85, 247),
    "build": QColor(34, 211, 238),
    "relic": QColor(251, 191, 36),
    "other": QColor(148, 163, 184),
    "error": QColor(248, 113, 113),
}
PILL_TEXT = {
    "idle": "WF-AI", "scan": "TARANIYOR…", "listen": "DİNLİYOR… 🎙",
    "world": "DÜNYA DURUMU", "other": "WF-AI", "error": "HATA",
}
TAG_TEXT = {"riven": "RIVEN", "build": "BUILD", "relic": "RELIC"}


def theme_hex(mode: str) -> str:
    return THEME.get(mode, THEME["other"]).name()


class PetWidget(QWidget):
    W, H = 380, 84

    def __init__(self, fps: int = 30, animations: bool = True):
        super().__init__()
        self.setFixedSize(self.W, self.H)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.state = "idle"
        self.t = 0.0
        self.interactive = False
        self.animations = animations
        self._timer = QTimer(self)
        self._timer.setInterval(max(10, int(1000 / max(1, fps))))
        self._timer.timeout.connect(self._tick)

    def set_state(self, state: str):
        self.state = state
        if self.animations and state != "idle":
            if not self._timer.isActive():
                self._timer.start()
        else:
            self._timer.stop()
        self.update()

    def _tick(self):
        self.t = (self.t + self._timer.interval() / 1000.0) % 3600.0
        self.update()

    # ---------- drawing ----------
    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self.state
        if s in ("riven", "build"):
            self._draw_crystal(p, THEME[s], TAG_TEXT[s])
        elif s == "relic":
            self._draw_eye(p, THEME[s], TAG_TEXT[s])
        else:
            self._draw_pill(p, s)
        p.end()

    def _glow(self, p, cx, cy, r, col):
        g = QRadialGradient(cx, cy, r)
        c1 = QColor(col); c1.setAlpha(int(70 + 25 * math.sin(self.t * 3)))
        c2 = QColor(col); c2.setAlpha(0)
        g.setColorAt(0, c1); g.setColorAt(1, c2)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), r, r)

    def _tag(self, p, text, col, x_end, cy):
        f = QFont("Consolas", 9); f.setBold(True)
        p.setFont(f)
        tw = p.fontMetrics().horizontalAdvance(text)
        r = QRectF(x_end - tw - 16, cy - 10, tw + 16, 20)
        p.setPen(QPen(col, 1)); p.setBrush(QColor(8, 13, 24, 215))
        p.drawRoundedRect(r, 4, 4)
        p.setPen(col.lighter(130))
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, text)

    def _outline(self, p, rect: QRectF):
        if self.interactive:
            pen = QPen(QColor(255, 255, 255, 120), 1, Qt.PenStyle.DashLine)
            p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(rect.adjusted(-3, -3, 3, 3), 8, 8)

    def _draw_pill(self, p, s):
        col = THEME.get(s, THEME["idle"])
        text = PILL_TEXT.get(s, "WF-AI")
        f = QFont("Consolas", 9); f.setBold(True)
        p.setFont(f)
        tw = p.fontMetrics().horizontalAdvance(text)
        w, h = tw + 36, 24
        x, y = self.W - w - 6, 6
        rect = QRectF(x, y, w, h)

        p.setPen(QPen(col, 1.2)); p.setBrush(QColor(8, 13, 24, 225))
        p.drawRoundedRect(rect, h / 2, h / 2)

        if s in ("scan", "listen"):
            span = w * 0.35
            pos = (self.t * 1.3 % 1.0) * (w + span) - span
            grad = QLinearGradient(x + pos, 0, x + pos + span, 0)
            a = QColor(col); a.setAlpha(0)
            b = QColor(col); b.setAlpha(80)
            grad.setColorAt(0, a); grad.setColorAt(0.5, b); grad.setColorAt(1, a)
            path = QPainterPath(); path.addRoundedRect(rect, h / 2, h / 2)
            p.save(); p.setClipPath(path); p.fillRect(rect, QBrush(grad)); p.restore()

        dot = QColor(col)
        if s != "idle":
            dot.setAlphaF(0.5 + 0.5 * abs(math.sin(self.t * 5)))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(dot)
        p.drawEllipse(QPointF(x + 13, y + h / 2), 4, 4)

        p.setPen(col.lighter(135))
        p.drawText(QRectF(x + 22, y, tw + 10, h),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
        self._outline(p, rect)

    def _draw_crystal(self, p, col, tag):
        cx, cy = self.W - 46, 42
        self._glow(p, cx, cy, 40, col)
        p.setBrush(Qt.BrushStyle.NoBrush)

        p.save(); p.translate(cx, cy); p.rotate(45 + self.t * 36)
        p.setPen(QPen(col, 2)); p.drawRect(QRectF(-23, -23, 46, 46)); p.restore()

        inner = col.lighter(140); inner.setAlpha(210)
        p.save(); p.translate(cx, cy); p.rotate(-self.t * 60)
        p.setPen(QPen(inner, 1.2)); p.drawRect(QRectF(-15, -15, 30, 30)); p.restore()

        k = 1 + 0.15 * math.sin(self.t * 4)
        p.save(); p.translate(cx, cy); p.rotate(45); p.scale(k, k)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(col.lighter(160))
        p.drawRect(QRectF(-6, -6, 12, 12)); p.restore()

        self._tag(p, tag, col, cx - 46, cy)
        self._outline(p, QRectF(cx - 40, cy - 40, 80, 80))

    def _draw_eye(self, p, col, tag):
        cx, cy = self.W - 46, 42
        self._glow(p, cx, cy, 40, col)
        p.setBrush(Qt.BrushStyle.NoBrush)

        pen = QPen(col, 2); pen.setStyle(Qt.PenStyle.DashLine)
        p.save(); p.translate(cx, cy); p.rotate(self.t * 30)
        p.setPen(pen); p.drawEllipse(QPointF(0, 0), 34, 34); p.restore()

        c2 = col.lighter(130); c2.setAlpha(170)
        pen2 = QPen(c2, 1.3); pen2.setStyle(Qt.PenStyle.DotLine)
        p.save(); p.translate(cx, cy); p.rotate(-self.t * 50)
        p.setPen(pen2); p.drawEllipse(QPointF(0, 0), 25, 25); p.restore()

        eye = QPainterPath()
        eye.moveTo(cx - 19, cy)
        eye.quadTo(cx, cy - 15, cx + 19, cy)
        eye.quadTo(cx, cy + 15, cx - 19, cy)
        p.setPen(QPen(col.lighter(120), 1.5)); p.setBrush(QColor(24, 12, 44, 220))
        p.drawPath(eye)

        r = 6 + 1.3 * math.sin(self.t * 3)
        iris = QRadialGradient(cx, cy, r + 3)
        iris.setColorAt(0, QColor(255, 250, 225))
        iris.setColorAt(0.45, col)
        iris.setColorAt(1, QColor(140, 70, 220, 0))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(iris))
        p.drawEllipse(QPointF(cx, cy), r + 3, r + 3)

        self._tag(p, tag, col, cx - 46, cy)
        self._outline(p, QRectF(cx - 40, cy - 40, 80, 80))


class OverlayWindow(QWidget):
    pet_clicked = pyqtSignal()
    dismissed = pyqtSignal()
    moved = pyqtSignal(int, int)

    def __init__(self, cfg: dict):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.cfg = cfg
        self.mode = "idle"

        self.pet = PetWidget(cfg.get("animation_fps", 30), cfg.get("animations", True))
        self.bubble = QLabel()
        self.bubble.setWordWrap(True)
        self.bubble.setTextFormat(Qt.TextFormat.RichText)
        self.bubble.setFixedWidth(372)
        self.bubble.hide()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 0, 4, 4)
        lay.setSpacing(2)
        lay.addWidget(self.pet, 0, Qt.AlignmentFlag.AlignRight)
        lay.addWidget(self.bubble, 0, Qt.AlignmentFlag.AlignRight)
        lay.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.go_idle)

        self._interact_vk = INTERACT_VK.get(str(cfg.get("interact_key", "alt")).lower(), 0x12)
        self._click_through = None
        self._key_timer = QTimer(self)
        self._key_timer.setInterval(100)
        self._key_timer.timeout.connect(self._poll_interact_key)

        self._press = None
        self._origin = QPoint()
        self._dragging = False

    # ---------- placement ----------
    def place(self):
        self.adjustSize()
        pos = self.cfg.get("position")
        if isinstance(pos, (list, tuple)) and len(pos) == 2:
            self.move(int(pos[0]), int(pos[1]))
        else:
            self.reset_position()

    def reset_position(self, screen_idx: int = -1):
        screens = QApplication.screens()
        if not screens:
            return
        if 0 <= screen_idx < len(screens):
            scr = screens[screen_idx]
        else:
            scr = self.screen() or QApplication.primaryScreen()
        geo = scr.availableGeometry()
        self.move(geo.right() - self.width() - 16, geo.top() + 40)

    def showEvent(self, e):
        super().showEvent(e)
        self._set_click_through(True)
        self._key_timer.start()

    # ---------- click-through ----------
    def _set_click_through(self, on: bool):
        if on == self._click_through:
            return
        hwnd = int(self.winId())
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style |= WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
        if style & WS_EX_LAYERED or on:
            style |= WS_EX_LAYERED
        style = (style | WS_EX_TRANSPARENT) if on else (style & ~WS_EX_TRANSPARENT)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        self._click_through = on
        self.pet.interactive = not on
        self.pet.update()

    def _poll_interact_key(self):
        down = bool(user32.GetAsyncKeyState(self._interact_vk) & 0x8000)
        if not down and self._press is not None:
            return  # finish an ongoing drag even if key released
        self._set_click_through(not down)

    # ---------- state ----------
    def set_state(self, state: str):
        self.mode = state
        if state in ("scan", "listen"):
            self._hide_timer.stop()
            self.bubble.hide()
        self.pet.set_state(state)
        self.adjustSize()

    def show_message(self, html: str, mode: str, seconds: int = 0):
        self.mode = mode
        col = theme_hex(mode)
        self.bubble.setStyleSheet(
            "QLabel {"
            "background-color: rgba(8, 12, 22, 235);"
            f"border: 1px solid {col};"
            f"border-left: 3px solid {col};"
            "border-radius: 8px; padding: 9px 11px;"
            "color: #e2e8f0; font-family: 'Segoe UI'; font-size: 10pt; }"
        )
        self.bubble.setText(html)
        self.bubble.show()
        self.pet.set_state(mode)
        self.adjustSize()
        self.raise_()
        if seconds and seconds > 0:
            self._hide_timer.start(int(seconds * 1000))
        else:
            self._hide_timer.stop()

    def go_idle(self):
        self._hide_timer.stop()
        self.bubble.hide()
        self.bubble.clear()
        self.mode = "idle"
        self.pet.set_state("idle")
        self.adjustSize()

    # ---------- mouse (only reachable while interact key is held) ----------
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._press = e.globalPosition().toPoint()
            self._origin = self.pos()
            self._dragging = False
        elif e.button() == Qt.MouseButton.RightButton:
            self.dismissed.emit()

    def mouseMoveEvent(self, e):
        if self._press is None:
            return
        d = e.globalPosition().toPoint() - self._press
        if not self._dragging and d.manhattanLength() > 5:
            self._dragging = True
        if self._dragging:
            self.move(self._origin + d)

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton or self._press is None:
            return
        if self._dragging:
            self.moved.emit(self.x(), self.y())
        elif self.bubble.isVisible() and self.bubble.geometry().contains(e.position().toPoint()):
            self.dismissed.emit()
        else:
            self.pet_clicked.emit()
        self._press = None
        self._dragging = False
