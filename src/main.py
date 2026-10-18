"""Warframe AI Overlay Assistant — entry point.

Flow: hotkey tap  -> RAM screenshot -> Gemini (auto-detect riven/relic/build) -> bubble
      hotkey hold -> RAM screenshot + mic (push-to-talk) -> Gemini -> bubble
Nothing is written to disk except config.json (settings / pet position).
"""
import ctypes
import html
import sys
import threading

from PyQt6.QtCore import QObject, QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap, QPolygonF
from PyQt6.QtWidgets import QApplication, QInputDialog, QLineEdit, QMenu, QSystemTrayIcon

import config
from ai_brain import AIBrain
from audio import MicRecorder
from capture import grab_screen_jpeg
from hotkey import HotkeyListener
from market_api import Market
from overlay_ui import OverlayWindow, theme_hex
from worldstate import WorldState


def esc(s) -> str:
    return html.escape(str(s or ""))


def position_labels(n: int):
    return {
        1: [""],
        2: ["Sol", "Sağ"],
        3: ["Sol", "Orta", "Sağ"],
        4: ["En Sol", "Sol-Orta", "Sağ-Orta", "En Sağ"],
    }.get(n, [f"#{i + 1}" for i in range(n)])


class Controller(QObject):
    sig_state = pyqtSignal(str)
    sig_message = pyqtSignal(str, str, int)

    def __init__(self, cfg: dict, window: OverlayWindow):
        super().__init__()
        self.cfg = cfg
        self.window = window
        self.brain = AIBrain(cfg)
        self.market = Market(cfg.get("platform", "pc"))
        self.world = WorldState(cfg.get("platform", "pc"))
        self.mic = MicRecorder()

        self._busy = False
        self._jpeg = None

        self.sig_state.connect(window.set_state)
        self.sig_message.connect(window.show_message)
        window.pet_clicked.connect(self.toggle_world)
        window.dismissed.connect(window.go_idle)
        window.moved.connect(self.save_position)

        self.hotkey = HotkeyListener(
            cfg.get("hotkey", "F9"), int(cfg.get("hold_threshold_ms", 350)),
            self._on_press, self._on_hold, self._on_release, self._on_hotkey_error,
        )
        self.hotkey.start()
        threading.Thread(target=self.brain.warmup, daemon=True).start()
        threading.Thread(target=self._preload_market, daemon=True).start()

    # ---------- background warmups ----------
    def _preload_market(self):
        try:
            self.market.load_items()
        except Exception:
            pass

    # ---------- hotkey callbacks (hotkey thread) ----------
    def _on_press(self):
        if self._busy:
            return
        self._busy = True
        try:
            self._jpeg = grab_screen_jpeg(
                int(self.cfg.get("monitor", 1)),
                int(self.cfg.get("max_capture_width", 1920)),
                int(self.cfg.get("jpeg_quality", 85)),
            )
        except Exception as e:
            self._jpeg = None
            self._busy = False
            self.sig_message.emit(f"Ekran yakalanamadı: {esc(e)}", "error", 8)
            return
        self.mic.start()
        self.sig_state.emit("scan")

    def _on_hold(self):
        if self._jpeg is not None and self.mic.available:
            self.sig_state.emit("listen")

    def _on_release(self, held: bool):
        if self._jpeg is None:
            return
        wav = self.mic.stop(keep=held)
        jpeg, self._jpeg = self._jpeg, None
        self.sig_state.emit("scan")
        threading.Thread(target=self._analyze, args=(jpeg, wav), daemon=True).start()

    def _on_hotkey_error(self, msg: str):
        self.sig_message.emit(esc(msg), "error", 12)

    # ---------- analysis (worker thread) ----------
    def _analyze(self, jpeg, wav):
        try:
            res = self.brain.analyze(jpeg, wav)
            jpeg = wav = None  # release screenshot/audio from RAM
            html_text, mode = self._render(res)
            self.sig_message.emit(html_text, mode, int(self.cfg.get("result_seconds", 25)))
        except Exception as e:
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                self.sig_message.emit(
                    "<b>Ücretsiz kota doldu</b><br>Biraz bekleyip tekrar dene (ücret çıkmaz, sadece limit).",
                    "error", 10)
                return
            if len(msg) > 300:
                msg = msg[:300] + "…"
            self.sig_message.emit(f"<b>Analiz başarısız</b><br>{esc(msg)}", "error", 12)
        finally:
            jpeg = wav = None
            self._busy = False

    def _render(self, res: dict):
        mode = res.get("mode", "other")
        if mode == "relic" and res.get("relic_items"):
            return self._render_relic(res), mode

        col = theme_hex(mode)
        out = f'<div style="font-size:11pt;font-weight:700;color:{col}">{esc(res.get("headline"))}</div>'
        lines = [l for l in res.get("lines", []) if str(l).strip()][:6]
        if lines:
            out += '<div style="margin-top:4px">' + "<br>".join(f"• {esc(l)}" for l in lines) + "</div>"
        if res.get("answer"):
            out += f'<div style="margin-top:6px;color:#cbd5e1">🎙️ {esc(res["answer"])}</div>'
        return out, mode

    def _render_relic(self, res: dict) -> str:
        names = [n for n in res.get("relic_items", []) if str(n).strip()][:4]
        items = self.market.evaluate(names)
        labels = position_labels(len(items))
        gold = theme_hex("relic")

        priced = [i for i in items if i["plat"] is not None]
        best = max(priced, key=lambda i: (i["plat"], i["ducats"] or 0)) if priced else None
        best_duc = max(items, key=lambda i: i["ducats"] or 0) if items else None

        if best:
            pos = labels[items.index(best)]
            head = f"🏆 SEÇ: {esc(best['name'])}" + (f" ({pos})" if pos else "")
        else:
            head = "Fiyat bulunamadı — isimler aşağıda"
        out = f'<div style="font-size:11pt;font-weight:700;color:{gold}">{head}</div><div style="margin-top:4px">'

        rows = []
        for idx, it in enumerate(items):
            plat = f"{it['plat']}p" if it["plat"] is not None else "?p"
            duc = f"{it['ducats']} duc" if it["ducats"] is not None else "- duc"
            pos = labels[idx]
            line = f"{esc(pos + ': ') if pos else ''}{esc(it['name'])} — <b>{plat}</b> | {duc}"
            if it is best:
                line = f'<span style="color:{gold}">{line}</span>'
            rows.append(line)
        out += "<br>".join(rows) + "</div>"

        if best_duc and best and best_duc is not best and (best_duc["ducats"] or 0) > (best["ducats"] or 0):
            out += (f'<div style="margin-top:4px;color:#94a3b8">🪙 Ducat için: '
                    f'{esc(best_duc["name"])} ({best_duc["ducats"]} duc)</div>')
        extra = [l for l in res.get("lines", []) if str(l).strip()][:2]
        if extra:
            out += '<div style="margin-top:4px;color:#94a3b8">' + "<br>".join(f"• {esc(l)}" for l in extra) + "</div>"
        if res.get("answer"):
            out += f'<div style="margin-top:6px;color:#cbd5e1">🎙️ {esc(res["answer"])}</div>'
        return out

    # ---------- world state (on click) ----------
    def toggle_world(self):
        if self.window.mode == "world" and self.window.bubble.isVisible():
            self.window.go_idle()
            return
        self.window.show_message("<i>Dünya durumu yükleniyor…</i>", "world", 0)
        threading.Thread(target=self._world_job, daemon=True).start()

    def _world_job(self):
        try:
            self.sig_message.emit(self.world.fetch_html(), "world", int(self.cfg.get("result_seconds", 25)) + 15)
        except Exception as e:
            self.sig_message.emit(f"Dünya durumu alınamadı: {esc(e)}", "error", 8)

    # ---------- settings ----------
    def save_position(self, x: int, y: int):
        self.cfg["position"] = [x, y]
        config.save(self.cfg)

    def reset_position(self):
        self.cfg["position"] = None
        config.save(self.cfg)
        self.window.reset_position()

    def ask_api_key(self):
        key, ok = QInputDialog.getText(
            None, "Gemini API Anahtarı",
            "Google AI Studio'dan aldığın Gemini API anahtarını yapıştır\n(https://aistudio.google.com/apikey):",
            QLineEdit.EchoMode.Password, self.cfg.get("gemini_api_key", ""),
        )
        if ok and key.strip():
            self.cfg["gemini_api_key"] = key.strip()
            config.save(self.cfg)
            self.brain.reset()
            threading.Thread(target=self.brain.warmup, daemon=True).start()

    def shutdown(self):
        self.hotkey.stop()


def make_icon() -> QIcon:
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(8, 13, 24))
    p.setPen(QColor(34, 211, 238))
    p.drawEllipse(2, 2, 60, 60)
    p.setBrush(QColor(34, 211, 238))
    p.drawPolygon(QPolygonF([QPointF(32, 12), QPointF(52, 32), QPointF(32, 52), QPointF(12, 32)]))
    p.end()
    return QIcon(pm)


def single_instance_guard():
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = k32.CreateMutexW(None, False, "WarframeAIAssistant_SingleInstance")
    if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
        sys.exit(0)
    return handle


def main():
    _mutex = single_instance_guard()  # noqa: F841 (keep handle alive)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Warframe AI Assistant")

    cfg = config.load()
    window = OverlayWindow(cfg)
    ctrl = Controller(cfg, window)

    tray = QSystemTrayIcon(make_icon(), app)
    tray.setToolTip(f"Warframe AI Asistanı — {cfg.get('hotkey')}: analiz, basılı tut: sesli soru")
    menu = QMenu()
    for text, fn in (
        ("🌍 Dünya Durumu", ctrl.toggle_world),
        ("🔑 API Anahtarını Ayarla", ctrl.ask_api_key),
        ("📍 Konumu Sıfırla", ctrl.reset_position),
    ):
        act = QAction(text, menu)
        act.triggered.connect(fn)
        menu.addAction(act)
    menu.addSeparator()
    quit_act = QAction("❌ Çıkış", menu)
    quit_act.triggered.connect(app.quit)
    menu.addAction(quit_act)
    tray.setContextMenu(menu)
    tray.show()

    window.place()
    window.show()

    if not cfg.get("gemini_api_key"):
        ctrl.ask_api_key()

    hk = esc(cfg.get("hotkey", "F9"))
    ik = esc(str(cfg.get("interact_key", "alt")).capitalize())
    window.show_message(
        f'<div style="font-weight:700;color:#34d399">Cephalon çevrimiçi, Tenno.</div>'
        f"• <b>{hk}</b> bas: ekranı analiz et (riven / relic / build otomatik)<br>"
        f"• <b>{hk}</b> basılı tut: sesli soru sor<br>"
        f"• <b>{ik}</b> basılıyken: sürükle / tıkla → dünya durumu / sağ tık kapat",
        "idle", 10,
    )

    app.aboutToQuit.connect(ctrl.shutdown)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
