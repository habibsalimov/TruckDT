#!/usr/bin/env python3
"""
Araç Kapısı - Kamera Test Scripti
Bu script kamera seçimi ve gerçek zamanlı araç tespiti için kullanılır.
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
    """Ana fonksiyon"""
    print("🚛 Araç Kapısı - Kamera Test Sistemi")
    print("=" * 50)
    
    try:
        # VehicleDetector'ı başlat
        print("🔧 Araç tespit sistemi başlatılıyor...")
        detector = VehicleDetector()
        print("✅ Sistem hazır!")
        
        print("\n📋 Menü:")
        print("1. Mevcut kameraları listele")
        print("2. Kamera seçip gerçek zamanlı tespit başlat")
        print("3. Belirli kamera ID ile tespit başlat")
        print("4. Çıkış")
        
        while True:
            try:
                choice = input("\nSeçiminizi yapın (1-4): ").strip()
                
                if choice == '1':
                    print("\n🔍 Kameralar taranıyor...")
                    cameras = detector.list_available_cameras()
                    if cameras:
                        print(f"\n✅ {len(cameras)} kamera bulundu:")
                        for cam in cameras:
                            print(f"   📹 Kamera {cam['id']}: {cam['resolution']} @ {cam['fps']}fps")
                    else:
                        print("❌ Hiç kamera bulunamadı!")
                
                elif choice == '2':
                    print("\n🎥 Kamera seçimi ve tespit başlatılıyor...")
                    detector.run_camera()
                
                elif choice == '3':
                    try:
                        camera_id = int(input("Kamera ID girin: "))
                        print(f"\n🎥 Kamera {camera_id} ile tespit başlatılıyor...")
                        detector.run_camera(camera_id=camera_id)
                    except ValueError:
                        print("❌ Geçersiz kamera ID! Sayı girin.")
                
                elif choice == '4':
                    print("👋 Çıkış yapılıyor...")
                    break
                
                else:
                    print("❌ Geçersiz seçim! 1-4 arası bir sayı girin.")
                    
            except KeyboardInterrupt:
                print("\n🛑 İşlem iptal edildi.")
                break
            except Exception as e:
                print(f"❌ Hata: {str(e)}")
    
    except Exception as e:
        print(f"❌ Sistem başlatma hatası: {str(e)}")
        print("💡 Gereksinimler yüklü mü kontrol edin:")
        print("   pip install opencv-python ultralytics")

if __name__ == "__main__":
    main() 