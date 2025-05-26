#!/usr/bin/env python3
"""
Özel Kamyon Tanıma Modeli Test Scripti
"""

import sys
import os
import logging

# Backend dizinini Python path'ine ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.vehicle_detector import VehicleDetector

# Logging ayarla
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Ana test fonksiyonu"""
    print("🚛 Özel Kamyon Tanıma Modeli Test Ediliyor...")
    print("=" * 60)
    
    try:
        # VehicleDetector'ı başlat
        print("🔧 VehicleDetector başlatılıyor...")
        detector = VehicleDetector()
        
        print("\n📊 Model Bilgileri:")
        print(f"   Özel Model: {detector.is_custom_model}")
        print(f"   Araç Sınıfları: {detector.vehicle_classes}")
        print(f"   Kamyon Sınıfları: {detector.truck_classes}")
        print(f"   Güven Eşiği: {detector.confidence_threshold}")
        
        if hasattr(detector, 'custom_classes'):
            print(f"   Model Sınıf Sayısı: {len(detector.custom_classes)}")
            print("   Tüm Sınıflar:")
            for class_id, class_name in detector.custom_classes.items():
                print(f"     {class_id}: {class_name}")
        
        # Model türünü kontrol et
        if detector.is_custom_model:
            print("\n✅ Özel kamyon tanıma modeli başarıyla yüklendi!")
            print("🎯 Model özel kamyon tespiti için optimize edilmiş")
        else:
            print("\n⚠️ Varsayılan YOLO modeli kullanılıyor")
            print("💡 Özel model yüklenemedi, genel araç tespiti yapılacak")
        
        # Kamera listesini test et
        print("\n📹 Mevcut kameralar:")
        cameras = detector.list_available_cameras()
        if cameras:
            for cam in cameras:
                print(f"   📷 Kamera {cam['id']}: {cam['resolution']} @ {cam['fps']}fps")
        else:
            print("   ❌ Hiç kamera bulunamadı")
        
        print("\n🎉 Test tamamlandı!")
        
    except Exception as e:
        print(f"\n❌ Test hatası: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 