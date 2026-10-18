# 🥷 Warframe AI Overlay Asistanı (Cephalon Pet)

Kısayola bastığında ekranı **sadece RAM'de** yakalayıp Gemini ile analiz eden, ekranda şekil değiştiren küçük bir Cephalon pet.

| Durum | Görünüm |
|---|---|
| Uyku / tarama | Minimalist HUD kapsül (yeşil) |
| Riven | Mor Cephalon kristali |
| Build / modlama | Mavi Cephalon kristali |
| Relic ödül ekranı | Altın Orokin Void gözü + canlı warframe.market fiyatları |

## 🛡️ Güvenlik (Ban riski)
- Oyunun belleğine / dosyalarına **hiç dokunmaz**: okuma yok, enjeksiyon yok, hook yok.
- Ekran görüntüsü OBS/Discord ile aynı yoldan alınır, kısayol Windows `RegisterHotKey` ile kaydedilir (klavye hook'u yok).
- Ekran görüntüsü ve ses **diske yazılmaz**; RAM'de JPEG/WAV olarak Gemini'a gider, sonra bellekten silinir.

## ⚡ Kurulum (format sonrası dahil)
1. Repoyu indir / `git clone`.
2. `setup_and_run.bat` dosyasına çift tıkla (Python yoksa winget ile kurar).
3. İlk açılışta Gemini API anahtarını iste: https://aistudio.google.com/apikey
4. Oyunu **Borderless Fullscreen** (Çerçevesiz) modda çalıştır.

Güncelleme: `update.bat` · Hata görmek için: `run_debug.bat`

## 🎮 Kullanım
- **F9 bas** → ekran analiz edilir; riven/relic/build otomatik algılanır.
- **F9 basılı tut ve konuş** → ekran + sesli sorun birlikte gönderilir.
- **Alt basılıyken**: pet'i sürükle, pet'e tıkla → dünya durumu, sağ tık → balonu kapat.
- Alt basılı değilken pet tamamen tıklama-geçirgendir (savaşta yanlışlıkla tıklanmaz).
- Sistem tepsisi simgesi: dünya durumu, API anahtarı, konum sıfırlama, çıkış.

## ⚙️ `config.json`
| Ayar | Açıklama |
|---|---|
| `model` | Gemini modeli (varsayılan `gemini-flash-latest`; daha derin analiz için bir Pro model) |
| `thinking_budget` | `null` = model varsayılanı; `0` = en hızlı (destekleyen modellerde) |
| `hotkey` | Örn. `F9`, `alt+q`, `ctrl+shift+r` |
| `interact_key` | `alt` / `ctrl` / `shift` |
| `monitor` | Hangi ekran (1 = birincil) |
| `max_capture_width` | Gönderilen görüntü genişliği (hız/kalite dengesi) |
| `result_seconds` | Cevap balonunun ekranda kalma süresi |
| `animations`, `animation_fps` | Animasyonlar (uykuda zaten durur) |
| `platform` | `pc`, `ps4`, `xb1`, `swi` |

## 📁 Yapı
```
src/main.py        Kontrolcü + tepsi
src/overlay_ui.py  Şekil değiştiren pet (QPainter)
src/capture.py     RAM-içi ekran yakalama
src/audio.py       Bas-konuş mikrofon (RAM)
src/hotkey.py      RegisterHotKey dinleyici
src/ai_brain.py    Gemini multimodal + otomatik mod algılama
src/market_api.py  warframe.market canlı fiyatlar
src/worldstate.py  Dünya durumu (tıklayınca)
```
