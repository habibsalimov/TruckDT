#!/bin/bash

echo "🚛 Araç Kapısı & Plaka Tespit Sistemi Kurulumu"
echo "=============================================="

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Hata kontrolü fonksiyonu
check_error() {
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Hata: $1${NC}"
        exit 1
    fi
}

echo -e "${BLUE}📋 Sistem gereksinimleri kontrol ediliyor...${NC}"

# Python kontrolü
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 bulunamadı. Lütfen Python 3.8+ yükleyin.${NC}"
    exit 1
fi

# Python versiyonu kontrolü
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${BLUE}🐍 Python versiyonu: $PYTHON_VERSION${NC}"

# Node.js kontrolü
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js bulunamadı. Lütfen Node.js 16+ yükleyin.${NC}"
    exit 1
fi

# npm kontrolü
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm bulunamadı. Lütfen npm yükleyin.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Sistem gereksinimleri tamam${NC}"

# Backend kurulumu
echo -e "${BLUE}🔧 Backend kurulumu başlıyor...${NC}"
cd backend

# Eski virtual environment varsa sil
if [ -d "venv" ]; then
    echo -e "${YELLOW}🗑️  Eski virtual environment siliniyor...${NC}"
    rm -rf venv
fi

# Python virtual environment oluştur
echo -e "${YELLOW}📦 Python virtual environment oluşturuluyor...${NC}"
python3 -m venv venv
check_error "Virtual environment oluşturulamadı"

# Virtual environment'ı aktifleştir
echo -e "${YELLOW}🔄 Virtual environment aktifleştiriliyor...${NC}"
source venv/bin/activate
check_error "Virtual environment aktifleştirilemedi"

# pip, setuptools ve wheel'i güncelle
echo -e "${YELLOW}🔧 Build araçları güncelleniyor...${NC}"
pip install --upgrade pip setuptools wheel
check_error "Build araçları güncellenemedi"

# Python paketlerini yükle
echo -e "${YELLOW}📦 Python paketleri yükleniyor...${NC}"
pip install -r requirements.txt
check_error "Python paketleri yüklenemedi"

# .env dosyası oluştur
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚙️ Environment dosyası oluşturuluyor...${NC}"
    cp env_template.txt .env
    echo -e "${YELLOW}⚠️  Lütfen .env dosyasını Supabase bilgilerinizle güncelleyin!${NC}"
fi

cd ..

# Frontend kurulumu
echo -e "${BLUE}🔧 Frontend kurulumu başlıyor...${NC}"
cd frontend

# Node.js paketlerini yükle
echo -e "${YELLOW}📦 Node.js paketleri yükleniyor...${NC}"
npm install
check_error "Node.js paketleri yüklenemedi"

cd ..

echo -e "${GREEN}🎉 Kurulum tamamlandı!${NC}"
echo ""
echo -e "${BLUE}📝 Sonraki adımlar:${NC}"
echo "1. Supabase hesabı oluşturun: https://supabase.com"
echo "2. Yeni bir proje oluşturun"
echo "3. backend/.env dosyasını Supabase bilgilerinizle güncelleyin"
echo "4. Supabase'de gerekli tabloları oluşturun:"
echo "   - Supabase Dashboard > SQL Editor'e gidin"
echo "   - docs/supabase-setup.sql dosyasının içeriğini kopyalayın ve çalıştırın"
echo ""
echo -e "${BLUE}🚀 Uygulamayı çalıştırmak için:${NC}"
echo ""
echo -e "${YELLOW}Terminal 1 (Backend):${NC}"
echo "cd backend"
echo "source venv/bin/activate"
echo "python app.py"
echo ""
echo -e "${YELLOW}Terminal 2 (Frontend):${NC}"
echo "cd frontend"
echo "npm start"
echo ""
echo -e "${GREEN}📱 Uygulama adresleri:${NC}"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:5000"
echo ""
echo -e "${YELLOW}⚠️  Notlar:${NC}"
echo "- Kamera erişimi için HTTPS gerekebilir (production'da)"
echo "- İlk çalıştırmada AI modelleri indirilecek (internet gerekli)"
echo "- Supabase bağlantısı için .env dosyasını mutlaka güncelleyin" 