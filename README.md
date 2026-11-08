# ✨ Instagram Media Optimizer (Ultra HD)

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: Non-Commercial](https://img.shields.io/badge/License-Non--Commercial-red.svg)](LICENSE)
[![Built with AI](https://img.shields.io/badge/Built%20with-AI%20%2F%20Antigravity-8a3ab9.svg)](https://github.com/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://github.com/)

> 🤖 **Not:** Bu proje, yapay zeka (AI) destekli eşli programlama ile tasarlanmış ve optimize edilmiştir.

Instagram'ın yükleme sırasında uyguladığı agresif ve kaliteyi bozan yeniden sıkıştırma algoritmasını bertaraf etmek amacıyla geliştirilmiş, modern kullanıcı arayüzüne sahip bağımsız bir medya optimizasyon uygulamasıdır.

Fotoğraf ve videolarınızı Instagram'ın algoritmalarına birebir uyan **sRGB**, **Lanczos Super-Sampling**, **Unsharp Mask** ve **H.264** standartlarında işler. Bu sayede Instagram sunucuları medyanızı kaba bir şekilde yeniden sıkıştırmaz; detay kaybı yaşanmaz ve renkler solmaz.

---

## 🚀 Öne Çıkan Özellikler

- **🔒 Orijinal Dosyaları Korur:** Seçilen dosyaların üzerine asla yazmaz. Çıktı dosyasını aynı klasöre dosya adının sonuna `_insta` ekleyerek üretir (Örn: `foto.jpg` ➔ `foto_insta.jpg`).
- **📦 Kurulum Gerektirmez (Portable):** `dist/InstagramOptimizer.exe` dosyasını doğrudan çalıştırabilir veya arkadaşlarınıza gönderebilirsiniz. Python veya ek yazılım kurulumu gerekmez.
- **✨ Akıllı Netleştirme (Unsharp Mask):** Boyutlandırma sonrası detayların yumuşamasını önler; göz, saç teli, kumaş ve doğa dokularındaki mikro-kontrastı açığa çıkarır.
- **🎨 Kusursuz Renkler (sRGB & 4:4:4):** iPhone veya kameraların `Display P3` / `Adobe RGB` profillerini Instagram uyumlu `sRGB`'ye dönüştürür. `Chroma 4:4:4` ile renk kenarlarında lekelenmeyi engeller.
- **📱 Hazır Format Şablonları:**
  - 📸 **Dikey Post (4:5 | 1080x1350):** Akışta en çok alan kaplayan, en yüksek etkileşimli format.
  - 🎬 **Reels & Hikaye (9:16 | 1080x1920):** Tam ekran dikey medya.
  - ⬛ **Kare Post (1:1 | 1080x1080):** Klasik kare fotoğraf.
  - 🖼️ **Yatay Post (1.91:1 | 1080x566):** Manzara çekimleri.
  - 📐 **Orijinal Oran Koruma:** En-boyu bozmadan maksimum genişliği 1080px'e sabitler.
- **🖼️ Akıllı Çerçeveleme:**
  - *Bulanık Arka Plan:* Fotoğrafı kırpmadan kenarlara estetik bulanık arka plan ekler.
  - *Kırparak Doldur (Crop & Fill):* Kareyi tam dolduracak şekilde akıllı ortalar.
  - *Siyah / Beyaz Çerçeve.*
- **🎥 Video Desteği:** H.264 High Profile (Level 4.2), YUV420p, BT.709 renk uzayı ve anında oynatma için `+faststart` (moov atomu optimizasyonu).

---

## 🛠️ Kurulum & Çalıştırma (Geliştiriciler İçin)

Projeyi kaynak koddan çalıştırmak veya düzenlemek isterseniz:

### 1. Depoyu Klonlayın
```bash
git clone https://github.com/KULLANICI_ADINIZ/instagram-media-optimizer.git
cd instagram-media-optimizer
```

### 2. Sanal Ortam Oluşturun ve Bağımlılıkları Yükleyin
```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Paketleri kurun:
pip install -r requirements.txt
```

### 3. Uygulamayı Başlatın
```bash
python app.py
```

---

## 📦 Kendi `.exe` Dosyanızı Derleme (Build)

Uygulamayı tek bir taşınabilir `.exe` dosyası haline getirmek için:

```bash
pyinstaller --noconsole --onefile --name "InstagramOptimizer" --collect-all customtkinter app.py
```
Oluşan çalıştırılabilir dosya `dist/InstagramOptimizer.exe` altında hazır olacaktır.

---

## 🔬 Teknik Detay: Neden Instagram'da Kalite Bozulmaz?

1. **Çözünürlük Çatışması Engellenir:** Instagram akışta genişliği maksimum 1080px kabul eder. 4K bir görsel gönderildiğinde Instagram'ın sunucu tarafındaki kaba küçültme filtresi detayları yutar. Önceden 1080px'e indirgendiğinde Instagram sunucusu ek sıkıştırma yapmaz.
2. **Lanczos Sinc Enterpolasyonu:** Piksel küçültme rastgele atlamalarla değil, 8x8 sinc matematiksel ağırlıklandırmasıyla yapılır. Bu sayede sensör gürültüsü nötrlenir ve gerçek doku öne çıkar.
3. **Chroma Subsampling (4:4:4 vs 4:2:0):** Standart JPEG sıkıştırmalarındaki %75 renk bilgisi kaybı (`4:2:0`) yerine tam renk örneklemesi (`4:4:4`) kullanılır.
4. **Moov Atom (+faststart):** Videolarda metaveri başa alınır, Instagram sunucusu videonun tamamını indirmeden anında işlemeye başlar.

---

## 📄 Lisans

Bu proje **Ticari Olmayan Özel Lisans (Non-Commercial License)** kapsamındadır. 
- Kişisel, eğitim ve kar amacı gütmeyen amaçlarla tamamen ücretsiz olarak kullanılabilir ve incelenebilir.
- **Ticari amaçla kullanılması, satılması veya gelir elde etmek amacıyla bir ürün/hizmet haline getirilmesi kesinlikle yasaktır.**
- Detaylar için [LICENSE](LICENSE) dosyasını inceleyebilirsiniz.
