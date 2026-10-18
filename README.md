# 🥷 Warframe AI Overlay Asistanı (Cephalon Pet) — Kullanım Kılavuzu

Warframe oynarken ekrana küçük bir **Cephalon / HUD** olarak yerleşen, oyun dosyalarına veya RAM'ine hiç dokunmayan (**%0 Ban Riski**), ekran görüntüsünü ve sesini diske kaydetmeden (**%100 RAM-içi**) analiz eden yapay zeka asistanın.

---

## ⌨️ Kısayollar ve Kontroller (Tam Liste)

Asistanı kullanmak için **tek bir ana tuş (`F9`)** ve **tek bir etkileşim tuşu (`Alt`)** vardır:

| Kısayol / Hareket | Ne İşe Yarar? | Detay |
| :--- | :--- | :--- |
| **`F9` (Bas-Çek)** | **🔍 Otomatik Ekran Analizi** | O an ekranda ne varsa (**Riven**, **Relic Ödülü** veya **Build/Modlama**) otomatik algılar, şekil değiştirir ve tavsiyesini verir. |
| **`F9` (Basılı Tut + Konuş)** | **🎙️ Sesli Soru Sor (Bas-Konuş)** | Tuşa basılı tuttuğun sürece mikrofonunu dinler (`DİNLİYOR... 🎙`). Tuşu bıraktığında **Ekran Görüntüsü + Sesini** birlikte gönderir. *(Örn: "Kanka bu rivenı satayım mı reroll mu atayım?")* |
| **`Alt + Sol Tık (Basılı Tutup Sürükle)`** | **✋ Pet'in Yerini Değiştir** | `Alt` tuşuna basılı tutarken Pet'i fareyle tutup ekranda istediğin köşeye sürükleyebilirsin. Bıraktığın yeri otomatik kaydeder. |
| **`Alt + Sol Tık (Pet'in Üstüne Tek Tık)`** | **🌍 Canlı Dünya Durumu** | `Alt` basılıyken Pet'in üzerine tıklarsan **Cetus (Gece/Gündüz)**, **Vallis**, **Cambion**, **Archon**, **Sortie**, **Steel Path** ve **Baro Ki'Teer** durumunu açar/kapatır. |
| **`Alt + Sağ Tık`** *(veya Balona Sol Tık)* | **❌ Cevap Balonunu Kapat** | Ekranda açık olan analiz/yazı balonunu beklemeden anında kapatır ve Pet'i uyku moduna alır. |

> **👻 Hayalet Modu (Click-Through) Nedir?**
> Normalde (`Alt` tuşuna basmıyorken) Pet tamamen **tıklama-geçirgendir**. Savaşın ortasında yanlışlıkla Pet'in veya yazı balonunun olduğu yere tıklasan bile fare tıklaman Pet'in içinden geçip doğrudan oyuna gider, oyunu alta atmaz! Sadece `Alt` tuşuna basılı tuttuğunda Pet'in etrafında ince kesikli bir çizgi belirir ve tıklanabilir olur.

---

## 🎨 Pet'in Şekil ve Renk Anlamları

Pet ekranda ne gördüğüne göre otomatik olarak şekil ve renk değiştirir:

1. **🟢 Yeşil Minimalist Kapsül (`WF-AI`):**
   - **Uyku Modu (Idle):** İşlemci ve ekran kartı tüketimi **%0**'dır. Kısayola basmanı bekler.
   - **Tarama / Dinleme (`TARANIYOR...` / `DİNLİYOR...`):** Kısayola bastığında yeşil ışık dalgası akar.
2. **🟣 Mor Cephalon Kristali (`RIVEN`):**
   - Ekranda bir Riven kartı, Kuva Reroll (Eski vs Yeni seçimi) veya Riven pazarı gördüğünde açılır.
   - **Ne Söyler:** Hangi roll'u seçmen gerektiğini (*"ESKİYİ TUT"* / *"YENİYİ AL"*), statların o silah için değerini (Crit/Status/Incarnon uyumu), negatifin zararsız olup olmadığını ve tahmini platin değerini yazar.
3. **🟡 Altın Orokin Void Gözü (`RELIC`):**
   - Void Fissure sonunda 4'lü Relic ödül ekranı geldiğinde açılır.
   - **Ne Söyler:** Ekrandaki Prime parçalarını okur, **warframe.market** üzerinden canlı Platinum ve Ducat değerlerini çeker ve en değerli parçayı `🏆 SEÇ: ... (En Sağ / Sol-Orta vb.)` şeklinde en tepede gösterir.
4. **🔵 Mavi Cephalon Kristali (`BUILD`):**
   - Arsenal / Upgrade (Modlama) ekranında bastığında açılır.
   - **Ne Söyler:** Silah veya Warframe dizilimindeki eksik çarpanları (Multishot, Element, Bane/Faction, Galvanized, Arcane vb.) ve *"Şu modu çıkar, yerine şunu tak"* tavsiyesini listeler.

---

## ⚡ Kurulum ve Başlatma (Format Sonrası Dahil)
1. **Oyunu Çerçevesiz Moda Al:** Warframe ayarlarından ekran modunu **Borderless Fullscreen (Çerçevesiz Tam Ekran)** yap.
2. **Başlat (`WF-AI.exe` veya `setup_and_run.bat`):**
   - Klasördeki mavi elmas simgeli **`WF-AI.exe`** (veya ilk kurulumda **`setup_and_run.bat`**) dosyasına çift tıkla.
   - Eğer ilk kez açıyorsan (veya format sonrasıysa), otomatik olarak Python sanal ortamını (`.venv`) kurar ve `WF-AI.exe` uygulamasını başlatır.
   - **Görev Yöneticisi (Task Manager):** Uygulama `python.exe` olarak değil, kendi özel simgesiyle doğrudan **`WF-AI` (`WF-AI.exe`)** olarak çalışır.
3. **API Anahtarı:** İlk açılışta gelen pencereye ücretsiz [Google AI Studio](https://aistudio.google.com/apikey) anahtarını yapıştır.
4. **Sistem Tepsisi (Saatin Yanı):** Sağ altta saatin yanındaki gizli simgeler (`^`) içinde **Mavi Elmas** ikonunu göreceksin. Ona sağ tıklayarak:
   - `🌍 Dünya Durumu`nu açabilir,
   - `🖥️ Diğer Monitöre Taşı` ile çift monitör kullanıyorsan Pet'i tek tıkla diğer ekranın sağ üst köşesine ışınlayabilir (Ayrıca `F9`'a bastığında Warframe hangi monitördeyse otomatik o monitörü okur!),
   - `🔑 API Anahtarını Ayarla`yabilir,
   - `📍 Konumu Sıfırla`yabilir,
   - `❌ Çıkış` ile asistanı tamamen kapatabilirsin.

---

## ⚙️ Kısayol Tuşunu veya Ayarları Değiştirme (`config.json`)

Kısayol tuşunu (`F9`) başka bir tuş yapmak istersen klasördeki **`config.json`** dosyasını Not Defteri ile açıp değiştirebilirsin:

```json
{
  "gemini_api_key": "AIzaSy...",
  "model": "gemini-flash-latest",
  "hotkey": "F9",
  "interact_key": "alt",
  "hold_threshold_ms": 350,
  "monitor": 1,
  "result_seconds": 25
}
```
- **`"hotkey"`:** `"F9"`, `"F10"`, `"alt+q"`, `"ctrl+shift+r"`, `` "`" `` gibi istediğin tuşu yazabilirsin.
- **`"interact_key"`:** Pet'i sürüklemek için basılı tutulan tuş (`"alt"`, `"ctrl"` veya `"shift"`).
- **`"result_seconds"`:** Cevap balonunun ekranda kaç saniye kalacağı (varsayılan `25` saniye).
- **`"monitor"`:** Çift monitör kullanıyorsan ve oyun 2. ekrandaysa `2` yapabilirsin.
*(Ayarları değiştirdikten sonra sağ alttaki tepsi simgesinden Çıkış yapıp `setup_and_run.bat` ile yeniden başlatman yeterlidir.)*

---

## 🛠️ Sorun Giderme ve Güncelleme
- **`run_debug.bat`:** Eğer bir şey çalışmazsa bu dosyayı çalıştır; siyah komut penceresi açık kalır ve varsa hata mesajını gösterir.
- **`update.bat`:** Projeyi GitHub'a yükledikten sonra güncellemeleri tek tıkla çekmek için kullanılır.
