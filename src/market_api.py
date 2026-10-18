"""warframe.market live prices (v2 API). Everything cached in memory only."""
import difflib
import re
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests


class Market:
    BASE = "https://api.warframe.market/v2"
    PRICE_TTL = 600  # seconds

    def __init__(self, platform: str = "pc"):
        self.s = requests.Session()
        self.s.headers.update({
            "User-Agent": "WarframeAIAssistant/1.0 (personal overlay)",
            "Accept": "application/json",
            "Language": "en",
            "Platform": platform,
            "Crossplay": "true",
        })
        self._items = None
        self._lock = threading.Lock()
        self._price_cache = {}

    @staticmethod
    def _norm(s: str) -> str:
        s = (s or "").lower().replace("\u2019", "'")
        s = re.sub(r"[^a-z0-9' ]+", " ", s)
        return re.sub(r"\s+", " ", s).strip()

    def load_items(self) -> dict:
        with self._lock:
            if self._items is not None:
                return self._items
            r = self.s.get(f"{self.BASE}/items", timeout=10)
            r.raise_for_status()
            items = {}
            for it in r.json().get("data", []):
                name = ((it.get("i18n") or {}).get("en") or {}).get("name")
                slug = it.get("slug")
                if name and slug:
                    items[self._norm(name)] = {"name": name, "slug": slug, "ducats": it.get("ducats")}
            self._items = items
            return items

    def match(self, raw: str):
        items = self.load_items()
        n = self._norm(raw)
        if not n:
            return None
        for cand in (n, f"{n} blueprint", n.replace(" blueprint", "")):
            if cand in items:
                return items[cand]
        keys = [k for k in items if "prime" in k] if "prime" in n else list(items)
        m = difflib.get_close_matches(n, keys, n=1, cutoff=0.82)
        return items[m[0]] if m else None

    def price(self, slug: str):
        now = time.time()
        cached = self._price_cache.get(slug)
        if cached and now - cached[0] < self.PRICE_TTL:
            return cached[1]
        r = self.s.get(f"{self.BASE}/orders/item/{slug}/top", timeout=8)
        r.raise_for_status()
        sells = (r.json().get("data") or {}).get("sell") or []
        prices = sorted(o["platinum"] for o in sells if isinstance(o.get("platinum"), (int, float)))
        val = int(round(statistics.median(prices[:5]))) if prices else None
        self._price_cache[slug] = (now, val)
        return val

    def evaluate(self, names):
        def one(raw):
            res = {"raw": raw, "name": raw, "plat": None, "ducats": None, "found": False}
            if "forma" in self._norm(raw):
                res.update(name="Forma Blueprint", plat=0, ducats=0, found=True)
                return res
            try:
                it = self.match(raw)
                if it:
                    res.update(name=it["name"], ducats=it.get("ducats"), found=True)
                    res["plat"] = self.price(it["slug"])
            except Exception as e:
                res["error"] = str(e)
            return res

        try:
            self.load_items()
        except Exception:
            pass
        with ThreadPoolExecutor(max_workers=3) as ex:
            return list(ex.map(one, names))
