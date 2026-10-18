"""Gemini multimodal brain: screenshot (+ optional voice) -> auto-detected mode + advice."""
import json
import threading
from typing import List, Optional

from pydantic import BaseModel

SYSTEM_PROMPT = """Sen "Cephalon" adında, Warframe'de uzman bir overlay asistanısın.
Oyuncu kısayola bastığında ekranının görüntüsü sana gelir. Türkçe, kısa, net ve samimi
("kanka" tonu, abartmadan) cevap ver. Ekranda çok az yer var:
- headline: en fazla ~60 karakter, net hüküm.
- lines: en fazla 5 madde, her biri en fazla ~90 karakter.

ÖNCE ekranı sınıflandır (mode alanı):
- "riven": Riven mod kartı, riven cycle/reroll ekranı (eski vs yeni stat seçimi), riven detayları
  veya riven ilanları (warframe.market / riven.market).
- "relic": Void Fissure / Relic ödül seçim ekranı (yan yana 1-4 ödül kartı) ya da relic ödül listesi.
- "build": Arsenal / Upgrade (modlama) ekranı, mod dizilimi, warframe/silah/companion build'i.
- "other": Diğer her şey.

RIVEN: Silah adını ve tüm pozitif/negatif statları sayılarıyla oku. Silaha göre meta statları
değerlendir (genelde CD, CC, MS, Dmg, elementler, SC; silahın crit/status/Incarnon yapısına göre).
Zararsız negatifleri belirt (ör. -Zoom, Slash silahta -Impact/-Puncture, -Ammo Max, bazı
silahlarda -Status Duration; faction negatiflerinde dikkatli ol). Reroll ekranındaysa headline'da
NET söyle: "ESKİYİ TUT" ya da "YENİYİ AL". Not ver: Çöp / Kullanılabilir / İyi / God Roll.
Mümkünse kaba bir platin aralığı ver ve "tahmini" olduğunu yaz. Stat isimlerini oyundaki
İngilizce kısaltmalarla yaz (CD, CC, MS, SC, Dmg, Fire Rate, Toxin...).

RELIC: Ödül kartlarındaki item isimlerini SOLDAN SAĞA, ekranda yazdığı gibi İngilizce ve TAM
olarak relic_items listesine yaz (ör. "Glaive Prime Blueprint", "Forma Blueprint",
"Saryn Prime Neuroptics"). İsim kesikse bildiğin tam ismi yaz. Fiyatları program
warframe.market'ten çekecek; headline kısa olsun ("Relic ödülleri okundu"). lines'a sadece
özel bir not varsa yaz (vaulted, set tamamlama vb.), yoksa boş bırak.

BUILD: Warframe/silahı ve takılı modları oku. Eksik çarpanları (base damage, multishot, crit,
elementler, Galvanized/Primed/faction modlar, Arcane'ler), gereksiz modları, kapasite/forma/
aura/exilus önerilerini söyle. Somut "X çıkar, Y tak" önerileri ver.

OTHER: Ekranda ne olduğunu 1 cümlede söyle ve faydalı bir ipucu ver.

SESLİ SORU: Ses eki varsa önce soruyu 'answer' alanında yanıtla (en fazla ~250 karakter),
ekranı bağlam olarak kullan. Ses yoksa answer boş string olsun.

Emin olmadığın şeyleri (güncel disposition, fiyat) uydurma; "tahmini" de."""


class Analysis(BaseModel):
    mode: str
    headline: str
    lines: List[str]
    relic_items: List[str]
    answer: str


class AIBrain:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self._client = None
        self._lock = threading.Lock()

    def reset(self):
        with self._lock:
            self._client = None

    def warmup(self):
        try:
            self._get_client()
        except Exception:
            pass

    def _get_client(self):
        with self._lock:
            if self._client is None:
                key = (self.cfg.get("gemini_api_key") or "").strip()
                if not key:
                    raise RuntimeError("Gemini API anahtarı yok. Tepsi simgesi → 'API Anahtarını Ayarla'.")
                from google import genai
                self._client = genai.Client(api_key=key)
            return self._client

    def analyze(self, jpeg: bytes, wav: Optional[bytes] = None) -> dict:
        from google.genai import types

        client = self._get_client()
        parts = [types.Part.from_bytes(data=jpeg, mime_type="image/jpeg")]
        if wav:
            parts.append(types.Part.from_bytes(data=wav, mime_type="audio/wav"))
            task = "Ekran görüntüsü ve kullanıcının sesli sorusu ekte. Ekranı sınıflandır, analiz et ve soruyu yanıtla."
        else:
            task = "Ekran görüntüsü ekte. Ekranı sınıflandır ve analiz et."
        parts.append(types.Part.from_text(text=task))

        gen_cfg = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=Analysis,
            temperature=0.4,
        )
        budget = self.cfg.get("thinking_budget")
        if budget is not None:
            gen_cfg.thinking_config = types.ThinkingConfig(thinking_budget=int(budget))

        primary = self.cfg.get("model") or "gemini-3.7-flash"
        fallback_models = [
            primary,
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3-flash-preview",
            "gemini-flash-lite-latest",
        ]
        # Keep order without duplicates
        models_to_try = list(dict.fromkeys(fallback_models))

        resp = None
        last_err = None
        for mdl in models_to_try:
            try:
                resp = client.models.generate_content(
                    model=mdl,
                    contents=[types.Content(role="user", parts=parts)],
                    config=gen_cfg,
                )
                break
            except Exception as e:
                last_err = e
                emsg = str(e)
                if any(code in emsg for code in ("429", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND", "400", "INVALID_ARGUMENT", "503", "UNAVAILABLE")):
                    continue
                raise
        del parts  # drop image/audio references ASAP
        if resp is None and last_err is not None:
            raise last_err

        parsed = getattr(resp, "parsed", None)
        if isinstance(parsed, BaseModel):
            data = parsed.model_dump()
        else:
            data = json.loads(resp.text or "{}")

        mode = str(data.get("mode", "other")).lower().strip()
        data["mode"] = mode if mode in ("riven", "relic", "build", "other") else "other"
        data.setdefault("lines", [])
        data.setdefault("relic_items", [])
        data.setdefault("answer", "")
        data.setdefault("headline", "")
        return data
