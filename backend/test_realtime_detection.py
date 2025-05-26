#!/usr/bin/env python3
"""
Real-Time Detection Test ve Kalibrasyon Scripti
"""

import sys
import os
import cv2
import time
import logging
import numpy as np

# Backend dizinini Python path'ine ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.vehicle_detector import VehicleDetector
from config.detection_config import DetectionConfig

# Logging ayarla
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class RealTimeDetectionTester:
    def __init__(self):
        self.detector = VehicleDetector()
        self.config = DetectionConfig()
        
    def test_stability(self, camera_id=1, duration=30):
        """Stabilite testi"""
        print(f"🧪 {duration} saniye stabilite testi başlatılıyor...")
        print("=" * 60)
        
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"❌ Kamera {camera_id} açılamadı!")
            return
        
        # Kamera ayarları
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.CAMERA_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, self.config.CAMERA_FPS)
        
        start_time = time.time()
        frame_count = 0
        detection_stats = {
            'total_detections': 0,
            'stable_detections': 0,
            'unstable_detections': 0,
            'false_positives': 0
        }
        
        print("📊 İstatistikler:")
        print("   ESC: Çıkış | S: Ekran görüntüsü | R: İstatistikleri sıfırla")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            current_time = time.time()
            
            # Tespit yap
            detections = self.detector.detect_frame(frame)
            
            # İstatistikleri güncelle
            for detection in detections:
                detection_stats['total_detections'] += 1
                stability = detection.get('stability_count', 0)
                
                if stability >= self.config.STABILITY_THRESHOLD:
                    detection_stats['stable_detections'] += 1
                else:
                    detection_stats['unstable_detections'] += 1
            
            # Çizim yap
            frame = self.detector.draw_detections(frame, detections)
            
            # İstatistik bilgilerini ekle
            elapsed_time = current_time - start_time
            fps = frame_count / elapsed_time if elapsed_time > 0 else 0
            
            # Bilgi metinleri
            info_lines = [
                f"FPS: {fps:.1f} | Frame: {frame_count}",
                f"Süre: {elapsed_time:.1f}s / {duration}s",
                f"Toplam Tespit: {detection_stats['total_detections']}",
                f"Kararlı: {detection_stats['stable_detections']}",
                f"Kararsız: {detection_stats['unstable_detections']}",
                f"Kararlılık Oranı: {(detection_stats['stable_detections'] / max(1, detection_stats['total_detections']) * 100):.1f}%"
            ]
            
            for i, line in enumerate(info_lines):
                y_pos = 30 + i * 25
                cv2.putText(frame, line, (10, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Progress bar
            progress = min(elapsed_time / duration, 1.0)
            bar_width = 400
            bar_height = 20
            bar_x = (frame.shape[1] - bar_width) // 2
            bar_y = frame.shape[0] - 40
            
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (100, 100, 100), -1)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + int(bar_width * progress), bar_y + bar_height), (0, 255, 0), -1)
            
            cv2.imshow("Real-Time Detection Test", frame)
            
            # Klavye kontrolü
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == ord('s'):
                timestamp = int(time.time())
                filename = f"detection_test_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                print(f"📸 Ekran görüntüsü kaydedildi: {filename}")
            elif key == ord('r'):
                detection_stats = {k: 0 for k in detection_stats.keys()}
                start_time = time.time()
                frame_count = 0
                print("🔄 İstatistikler sıfırlandı")
            
            # Test süresi doldu mu?
            if elapsed_time >= duration:
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Final raporu
        print("\n" + "=" * 60)
        print("📊 TEST RAPORU")
        print("=" * 60)
        print(f"Test Süresi: {elapsed_time:.1f} saniye")
        print(f"İşlenen Frame: {frame_count}")
        print(f"Ortalama FPS: {frame_count / elapsed_time:.1f}")
        print(f"Toplam Tespit: {detection_stats['total_detections']}")
        print(f"Kararlı Tespit: {detection_stats['stable_detections']}")
        print(f"Kararsız Tespit: {detection_stats['unstable_detections']}")
        
        if detection_stats['total_detections'] > 0:
            stability_ratio = detection_stats['stable_detections'] / detection_stats['total_detections'] * 100
            print(f"Kararlılık Oranı: {stability_ratio:.1f}%")
            
            if stability_ratio >= 80:
                print("✅ Mükemmel kararlılık!")
            elif stability_ratio >= 60:
                print("🟡 İyi kararlılık")
            else:
                print("🔴 Kararlılık iyileştirmesi gerekli")
        
        print("=" * 60)
    
    def calibrate_parameters(self, camera_id=1):
        """Parametre kalibrasyonu"""
        print("🔧 Parametre Kalibrasyonu")
        print("=" * 60)
        print("Kontroller:")
        print("  Q/A: Confidence threshold (±0.05)")
        print("  W/S: NMS threshold (±0.05)")
        print("  E/D: Smoothing factor (±0.05)")
        print("  R/F: Stability threshold (±1)")
        print("  ESC: Çıkış")
        print("=" * 60)
        
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"❌ Kamera {camera_id} açılamadı!")
            return
        
        # Başlangıç değerleri
        conf_threshold = self.config.CONFIDENCE_THRESHOLD
        nms_threshold = self.config.NMS_THRESHOLD
        smoothing_factor = self.config.SMOOTHING_FACTOR
        stability_threshold = self.config.STABILITY_THRESHOLD
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Parametreleri güncelle
            self.detector.confidence_threshold = conf_threshold
            self.detector.nms_threshold = nms_threshold
            
            # Tespit yap
            detections = self.detector.detect_frame(frame)
            frame = self.detector.draw_detections(frame, detections)
            
            # Parametre bilgilerini göster
            param_lines = [
                f"Confidence: {conf_threshold:.2f} (Q/A)",
                f"NMS: {nms_threshold:.2f} (W/S)",
                f"Smoothing: {smoothing_factor:.2f} (E/D)",
                f"Stability: {stability_threshold} (R/F)",
                f"Detections: {len(detections)}"
            ]
            
            for i, line in enumerate(param_lines):
                cv2.putText(frame, line, (10, 30 + i * 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            cv2.imshow("Parameter Calibration", frame)
            
            # Klavye kontrolü
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == ord('q'):
                conf_threshold = min(0.9, conf_threshold + 0.05)
            elif key == ord('a'):
                conf_threshold = max(0.1, conf_threshold - 0.05)
            elif key == ord('w'):
                nms_threshold = min(0.9, nms_threshold + 0.05)
            elif key == ord('s'):
                nms_threshold = max(0.1, nms_threshold - 0.05)
            elif key == ord('e'):
                smoothing_factor = min(0.95, smoothing_factor + 0.05)
            elif key == ord('d'):
                smoothing_factor = max(0.1, smoothing_factor - 0.05)
            elif key == ord('r'):
                stability_threshold = min(10, stability_threshold + 1)
            elif key == ord('f'):
                stability_threshold = max(1, stability_threshold - 1)
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Optimal parametreleri kaydet
        print("\n🎯 Optimal Parametreler:")
        print(f"CONFIDENCE_THRESHOLD = {conf_threshold:.2f}")
        print(f"NMS_THRESHOLD = {nms_threshold:.2f}")
        print(f"SMOOTHING_FACTOR = {smoothing_factor:.2f}")
        print(f"STABILITY_THRESHOLD = {stability_threshold}")

def main():
    """Ana fonksiyon"""
    print("🚛 Real-Time Detection Test Sistemi")
    print("=" * 60)
    
    tester = RealTimeDetectionTester()
    
    while True:
        print("\n📋 Test Menüsü:")
        print("1. Stabilite Testi (30 saniye)")
        print("2. Parametre Kalibrasyonu")
        print("3. Hızlı Test (10 saniye)")
        print("4. Çıkış")
        
        try:
            choice = input("\nSeçiminizi yapın (1-4): ").strip()
            
            if choice == '1':
                tester.test_stability(duration=30)
            elif choice == '2':
                tester.calibrate_parameters()
            elif choice == '3':
                tester.test_stability(duration=10)
            elif choice == '4':
                print("👋 Çıkış yapılıyor...")
                break
            else:
                print("❌ Geçersiz seçim!")
                
        except KeyboardInterrupt:
            print("\n🛑 Test iptal edildi.")
            break
        except Exception as e:
            print(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    main() 