"""On-demand world state (only fetched when you click the pet)."""
import html

import requests


def _e(s):
    return html.escape(str(s if s is not None else "?"))


class WorldState:
    def __init__(self, platform: str = "pc"):
        self.url = f"https://api.warframestat.us/{platform}/?language=en"
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "WarframeAIAssistant/1.0"

    def fetch_html(self) -> str:
        r = self.s.get(self.url, timeout=8)
        r.raise_for_status()
        d = r.json()
        rows = []

        c = d.get("cetusCycle") or {}
        if c:
            rows.append(("🌅 Cetus", f'{"Gündüz" if c.get("isDay") else "Gece"} — {c.get("timeLeft", "?")}'))
        v = d.get("vallisCycle") or {}
        if v:
            rows.append(("❄️ Vallis", f'{"Sıcak" if v.get("isWarm") else "Soğuk"} — {v.get("timeLeft", "?")}'))
        cb = d.get("cambionCycle") or {}
        if cb:
            state = str(cb.get("state") or cb.get("active") or "?").upper()
            rows.append(("🦠 Cambion", f'{state} — {cb.get("timeLeft", "?")}'))
        a = d.get("archonHunt") or {}
        if a:
            missions = ", ".join(str(m.get("type", "?")) for m in (a.get("missions") or []))
            rows.append(("👹 Archon", f'{a.get("boss", "?")} — {missions}'))
        s = d.get("sortie") or {}
        if s:
            rows.append(("⚔️ Sortie", f'{s.get("boss", "?")} ({s.get("faction", "?")})'))
        sp = d.get("steelPath") or {}
        if sp:
            reward = (sp.get("currentReward") or {}).get("name", "?")
            rows.append(("🔥 Steel Path", f'{reward} — {sp.get("remaining", "?")}'))
        fis = d.get("fissures") or []
        if fis:
            hard = sum(1 for f in fis if f.get("isHard"))
            storm = sum(1 for f in fis if f.get("isStorm"))
            rows.append(("🌀 Fissure", f"{len(fis)} aktif ({hard} Steel Path, {storm} Railjack)"))
        vt = d.get("voidTrader") or {}
        if vt:
            if vt.get("active"):
                rows.append(("🧳 Baro", f'{vt.get("location", "?")} — kalan {vt.get("endString", "?")}'))
            else:
                rows.append(("🧳 Baro", f'Geliş: {vt.get("startString", "?")}'))

        body = "".join(
            f'<tr><td style="padding:2px 10px 2px 0;color:#94a3b8;white-space:nowrap">{_e(k)}</td>'
            f'<td style="padding:2px 0">{_e(val)}</td></tr>'
            for k, val in rows
        )
        return (
            '<div style="font-weight:700;color:#34d399;margin-bottom:4px">🌍 DÜNYA DURUMU</div>'
            f"<table cellspacing=0 cellpadding=0>{body}</table>"
        )
