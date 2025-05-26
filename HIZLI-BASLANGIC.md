# 🚀 Hızlı Başlangıç Kılavuzu

Bu kılavuz, Araç Kapısı & Plaka Tespit Sistemi'ni hızlıca çalıştırmanız için gerekli adımları içerir.

## ⚡ 5 Dakikada Kurulum

### 1. Otomatik Kurulum

```bash
# Proje dizinine gidin
cd arac-kapisi-plaka-tespit

# Kurulum scriptini çalıştırın
chmod +x setup.sh
./setup.sh
```

### 2. Supabase Kurulumu (2 dakika)

1. [supabase.com](https://supabase.com) adresine gidin
2. "Start your project" → "New project" tıklayın
3. Proje adı girin (örn: "arac-kapisi-sistemi")
4. Şifre belirleyin ve "Create new project" tıklayın
5. Project Settings → API'ye gidin
6. **Project URL** ve **anon public** key'i kopyalayın

### 3. Environment Ayarları (30 saniye)

```bash
# Backend dizinine gidin
cd backend

# .env dosyasını düzenleyin
nano .env
```

Aşağıdaki bilgileri güncelleyin:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
```

### 4. Veritabanı Tabloları (1 dakika)

1. Supabase Dashboard'a gidin
2. Sol menüden **SQL Editor** seçin
3. `docs/supabase-setup.sql` dosyasını açın
4. İçeriği kopyalayıp SQL Editor'e yapıştırın
5. **Run** butonuna tıklayın

### 5. Sistemi Başlatın (30 saniye)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

## 🎯 İlk Kullanım

1. Tarayıcıda http://localhost:3000 adresine gidin
2. **"Kamerayı Başlat"** butonuna tıklayın
3. Kamera izni verin
4. **"Plaka Yönetimi"** sayfasına gidin
5. Test plakası ekleyin (örn: **34ABC1234**)
6. Ana sayfaya dönün ve sistemi test edin

## 🔧 Hızlı Test

### Test Plakası Ekleme
```bash
# API ile test plakası ekleyin
curl -X POST http://localhost:5000/api/plates \
  -H "Content-Type: application/json" \
  -d '{"plate_number": "34ABC1234"}'
```

### Sistem Sağlık Kontrolü
```bash
curl http://localhost:5000/api/health
```

## ⚠️ Yaygın Sorunlar ve Çözümler

### Problem: Python paket hatası
```bash
# Çözüm
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Problem: Kamera açılmıyor
- Tarayıcı izinlerini kontrol edin
- Başka uygulamaların kamerayı kullanmadığından emin olun
- HTTPS gerekebilir (localhost'ta genelde sorun yok)

### Problem: Supabase bağlantı hatası
- `.env` dosyasındaki URL ve KEY'i kontrol edin
- Supabase projesinin aktif olduğundan emin olun

### Problem: AI modeli indirilmiyor
- İnternet bağlantınızı kontrol edin
- İlk çalıştırmada YOLOv8 modeli otomatik indirilir

## 📱 Hızlı API Testleri

### Plaka Listesi
```bash
curl http://localhost:5000/api/plates
```

### Plaka Ekleme
```bash
curl -X POST http://localhost:5000/api/plates \
  -H "Content-Type: application/json" \
  -d '{"plate_number": "06XYZ9876"}'
```

### Plaka Kontrolü
```bash
curl -X POST http://localhost:5000/api/check-plate \
  -H "Content-Type: application/json" \
  -d '{"plate_number": "34ABC1234"}'
```

## 🎨 Hızlı Özelleştirme

### Tespit Sıklığını Değiştirme
`frontend/src/components/CameraStream.js` dosyasında:
```javascript
// 2 saniyede bir tespit (varsayılan)
setInterval(() => {
  captureAndDetect();
}, 2000); // Bu değeri değiştirin
```

### Kapı Animasyon Süresini Değiştirme
`frontend/src/components/GateAnimation.js` dosyasında:
```javascript
transition: { duration: 1 } // Saniye cinsinden
```

## 📊 Sistem Durumu Kontrolü

### Backend Durumu
- ✅ http://localhost:5000/api/health
- ✅ Terminal'de hata mesajı yok

### Frontend Durumu  
- ✅ http://localhost:3000 açılıyor
- ✅ Kamera butonu görünüyor

### Supabase Durumu
- ✅ Plaka ekleme/silme çalışıyor
- ✅ API yanıt veriyor

## 🚀 Production'a Hazırlık

1. **HTTPS** kullanın
2. **Environment** değişkenlerini güvenli tutun
3. **Supabase RLS** politikalarını sıkılaştırın
4. **Rate limiting** ekleyin
5. **Monitoring** kurun

## 📞 Yardım

- 📖 Detaylı dokümantasyon: `README.md`
- 🐛 Sorun bildirimi: GitHub Issues
- 💬 Soru-cevap: Discussions

---

**🎉 Tebrikler!** Sisteminiz çalışır durumda. Artık araç kapısı kontrolünü web üzerinden yapabilirsiniz! 