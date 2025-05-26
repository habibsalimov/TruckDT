# Web Tabanlı Otopark Kapısı & Plaka Tespit Sistemi

Bu proje, web tabanlı bir araç kapısı kontrol sistemidir. Kamera görüntüsünden araç tespiti yaparak, kamyon/tır plaklarını okur ve Supabase veritabanında kontrol ederek kapı açma kararı verir.

## 🚀 Özellikler

- **Canlı Kamera Görüntüsü**: Web kamerası ile gerçek zamanlı araç tespiti
- **Araç Tipi Tespiti**: Kamyon, tır ve diğer araçları ayırt etme
- **Plaka Okuma (OCR)**: Tespit edilen araç plakalarını otomatik okuma
- **Supabase Entegrasyonu**: Bulut tabanlı veritabanı ile plaka yönetimi
- **Görsel Bildirimler**: Kapı açıldı animasyonları ve uyarılar
- **Plaka Yönetimi**: Web arayüzü ile plaka ekleme/silme/güncelleme

## 🏗️ Proje Yapısı

```
arac-kapisi-plaka-tespit/
├── backend/                 # Python API sunucusu
│   ├── app.py              # Ana Flask uygulaması
│   ├── models/             # AI modelleri
│   ├── supabase/           # Veritabanı işlemleri
│   ├── utils/              # Yardımcı fonksiyonlar
│   └── requirements.txt    # Python bağımlılıkları
├── frontend/               # React web uygulaması
│   ├── src/
│   │   ├── components/     # React bileşenleri
│   │   ├── pages/          # Sayfa bileşenleri
│   │   └── App.js          # Ana uygulama
│   └── package.json        # Node.js bağımlılıkları
├── docs/                   # Dokümantasyon
└── setup.sh               # Otomatik kurulum scripti
```

## 🛠️ Teknolojiler

- **Frontend**: React.js, Material-UI, Framer Motion, React Webcam
- **Backend**: Python Flask, OpenCV, YOLOv8, EasyOCR
- **Veritabanı**: Supabase (PostgreSQL)
- **AI/ML**: Ultralytics YOLOv8 (araç tespiti), EasyOCR (plaka okuma)

## 📦 Kurulum

### Otomatik Kurulum (Önerilen)

```bash
chmod +x setup.sh
./setup.sh
```

### Manuel Kurulum

#### Sistem Gereksinimleri
- Python 3.8+ (Python 3.12 önerilir)
- Node.js 16+
- npm veya yarn

#### Backend Kurulumu

```bash
cd backend

# Virtual environment oluştur
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Build araçlarını güncelle
pip install --upgrade pip setuptools wheel

# Paketleri yükle
pip install -r requirements.txt

# Environment dosyası oluştur
cp env_template.txt .env
```

#### Frontend Kurulumu

```bash
cd frontend
npm install
```

## 🔧 Yapılandırma

### 1. Supabase Kurulumu

1. [Supabase](https://supabase.com) hesabı oluşturun
2. Yeni bir proje oluşturun
3. Project Settings > API'den URL ve anon key'i alın

### 2. Environment Dosyası

`backend/.env` dosyasını düzenleyin:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
FLASK_ENV=development
FLASK_DEBUG=True
```

### 3. Veritabanı Tabloları

Supabase Dashboard > SQL Editor'de `docs/supabase-setup.sql` dosyasının içeriğini çalıştırın.

## 🚀 Çalıştırma

### Backend Sunucusu

```bash
cd backend
source venv/bin/activate
python app.py
```

Backend: http://localhost:5000

### Frontend Sunucusu

```bash
cd frontend
npm start
```

Frontend: http://localhost:3000

## 🎯 Kullanım

1. Web arayüzüne gidin (http://localhost:3000)
2. Kamera izinlerini verin
3. "Kamerayı Başlat" butonuna tıklayın
4. Sistem otomatik olarak araç tespiti yapar
5. Kamyon/tır tespit edildiğinde plaka okuma başlar
6. Kayıtlı plaka ise kapı açılır animasyonu gösterilir
7. "Plaka Yönetimi" sayfasından yeni plakalar ekleyebilirsiniz

## 📱 API Endpointleri

- `GET /api/health` - Sistem sağlık kontrolü
- `POST /api/detect` - Görüntüden araç ve plaka tespiti
- `GET /api/plates` - Kayıtlı plakaları getir
- `POST /api/plates` - Yeni plaka ekle
- `DELETE /api/plates/:id` - Plaka sil
- `POST /api/check-plate` - Plaka kontrolü ve kapı açma

## 🔧 Sorun Giderme

### Python Paket Kurulum Hataları

**Problem**: `setuptools.build_meta` hatası
**Çözüm**:
```bash
pip install --upgrade pip setuptools wheel
```

**Problem**: NumPy uyumluluk hatası
**Çözüm**:
```bash
pip install numpy>=1.24.0 --force-reinstall
```

### Kamera Erişim Sorunları

- HTTPS gerekebilir (production'da)
- Tarayıcı izinlerini kontrol edin
- Kamera başka uygulamada kullanılıyor olabilir

### Supabase Bağlantı Sorunları

- `.env` dosyasındaki URL ve KEY'i kontrol edin
- Supabase projesinin aktif olduğundan emin olun
- RLS politikalarını kontrol edin

### AI Model İndirme Sorunları

- İlk çalıştırmada YOLOv8 modeli otomatik indirilir
- İnternet bağlantısı gereklidir
- Firewall ayarlarını kontrol edin

## 🎨 Özelleştirme

### Kapı Animasyonları
`frontend/src/components/GateAnimation.js` dosyasında Framer Motion animasyonları

### Araç Tespit Modeli
`backend/utils/vehicle_detector.py` dosyasında YOLOv8 ayarları

### Plaka Okuma Ayarları
`backend/utils/plate_reader.py` dosyasında EasyOCR konfigürasyonu

### UI Temaları
`frontend/src/App.js` dosyasında Material-UI tema ayarları

## 📊 Performans Optimizasyonu

- **GPU Kullanımı**: CUDA destekli GPU varsa `gpu=True` ayarlayın
- **Model Boyutu**: YOLOv8n (nano) yerine YOLOv8s (small) kullanabilirsiniz
- **Tespit Sıklığı**: `CameraStream.js`'de interval süresini ayarlayın
- **Görüntü Kalitesi**: Webcam çözünürlüğünü düşürün

## 🔒 Güvenlik

- Production'da HTTPS kullanın
- Supabase RLS politikalarını sıkılaştırın
- API rate limiting ekleyin
- Environment değişkenlerini güvenli tutun

## 📄 Lisans

MIT License

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📞 Destek

Sorunlarınız için GitHub Issues kullanın veya dokümantasyonu kontrol edin. 