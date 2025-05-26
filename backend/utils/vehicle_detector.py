import cv2 # type: ignore
import numpy as np # type: ignore
import logging
from ultralytics import YOLO # type: ignore
import os
import time
from collections import deque
import math
import sys

# Config dosyasını import et
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.detection_config import DetectionConfig

logger = logging.getLogger(__name__)

class VehicleDetector:
    def __init__(self, model_path=None):
        """
        Araç tespit sınıfını başlat
        """
        try:
            # Konfigürasyonu yükle
            self.config = DetectionConfig()
            
            # Özel model yolunu belirle
            if model_path is None:
                # Önce en iyi eğitilmiş modeli kontrol et
                best_model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'runs', 'detect', 'train2', 'weights', 'best.pt')
                custom_model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'vehicle_detection.pt')
                
                if os.path.exists(best_model_path):
                    model_path = best_model_path
                    logger.info(f"🏆 En iyi eğitilmiş model bulundu: {model_path}")
                elif os.path.exists(custom_model_path):
                    model_path = custom_model_path
                    logger.info(f"🚛 Özel kamyon tanıma modeli bulundu: {model_path}")
                else:
                    logger.info("⚠️ Özel model bulunamadı, varsayılan model kullanılacak")
            
            # YOLOv8 modelini yükle
            if model_path and os.path.exists(model_path):
                self.model = YOLO(model_path)
                self.is_custom_model = True
                logger.info(f"✅ Özel model yüklendi: {model_path}")
                
                # Model bilgilerini al
                try:
                    model_info = self.model.info()
                    logger.info(f"📊 Model bilgileri: {model_info}")
                except:
                    logger.info("📊 Model bilgileri alınamadı")
                
            else:
                # Varsayılan YOLOv8 modelini kullan
                self.model = YOLO('yolov8n.pt')  # nano model (hızlı)
                self.is_custom_model = False
                logger.info("✅ Varsayılan YOLOv8n modeli yüklendi")
            
            # Araç sınıfları (COCO dataset için varsayılan)
            self.vehicle_classes = {
                2: 'car',
                3: 'motorcycle', 
                5: 'bus',
                7: 'truck',
                # Özel model için ek sınıflar eklenebilir
            }
            
            # Eğer özel model ise, sınıf isimlerini modelden al
            if self.is_custom_model and hasattr(self.model, 'names'):
                model_names = self.model.names
                logger.info(f"🏷️ Model sınıf isimleri: {model_names}")
                
                # Özel model sınıflarını güncelle
                self.custom_classes = model_names
                # Kamyon/araç sınıflarını tespit et
                self.vehicle_classes = {}
                for class_id, class_name in model_names.items():
                    if any(keyword in class_name.lower() for keyword in ['truck', 'lorry', 'kamyon', 'tır', 'vehicle', 'car', 'bus', 'motorcycle']):
                        self.vehicle_classes[class_id] = class_name.lower()
                
                logger.info(f"🚗 Tespit edilecek araç sınıfları: {self.vehicle_classes}")
            
            # Kamyon/tır olarak kabul edilecek sınıflar
            self.truck_classes = ['truck', 'lorry', 'kamyon', 'tır', 'bus']
            
            # Konfigürasyondan parametreleri al
            self.confidence_threshold = self.config.CONFIDENCE_THRESHOLD
            self.nms_threshold = self.config.NMS_THRESHOLD
            self.min_detection_area = self.config.MIN_DETECTION_AREA
            
            # Stabilizasyon için tracking
            self.detection_history = deque(maxlen=self.config.HISTORY_SIZE)
            self.stable_detections = {}  # Kararlı tespitler
            self.detection_id_counter = 0
            
            # FPS hesaplama için
            self.fps_counter = 0
            self.fps_start_time = time.time()
            
            # Frame stabilizasyon
            self.frame_skip = 0  # Frame atlama sayacı
            self.process_every_n_frames = self.config.PROCESS_EVERY_N_FRAMES
            
            # Model test et
            self._test_model()
            
        except Exception as e:
            logger.error(f"❌ Model yükleme hatası: {str(e)}")
            # Fallback: Basit araç tespiti
            self.model = None
            self.use_fallback = True
            self.is_custom_model = False
    
    def _test_model(self):
        """Model test et"""
        try:
            logger.info("🧪 Model test ediliyor...")
            
            # Test görüntüsü oluştur (640x480 siyah görüntü)
            test_image = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Model ile test yap
            results = self.model(test_image, verbose=False, conf=self.confidence_threshold)
            
            logger.info("✅ Model test başarılı!")
            
            # Model sınıflarını logla
            if hasattr(self.model, 'names'):
                class_names = self.model.names
                logger.info(f"📋 Model sınıfları ({len(class_names)} adet):")
                for class_id, class_name in class_names.items():
                    logger.info(f"   {class_id}: {class_name}")
            
        except Exception as e:
            logger.error(f"❌ Model test hatası: {str(e)}")
            raise e
    
    def _calculate_iou(self, box1, box2):
        """İki bounding box arasındaki IoU (Intersection over Union) hesapla"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        # Kesişim alanı
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        
        # Birleşim alanı
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _smooth_detection(self, current_detections):
        """Tespit sonuçlarını yumuşat ve stabilize et"""
        smoothed_detections = []
        
        for detection in current_detections:
            bbox = detection['bbox']
            class_id = detection['class_id']
            confidence = detection['confidence']
            
            # Minimum alan kontrolü
            area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            if area < self.min_detection_area:
                continue
            
            # Geçmiş tespitlerle karşılaştır
            best_match = None
            best_iou = 0.0
            
            for stable_id, stable_detection in self.stable_detections.items():
                iou = self._calculate_iou(bbox, stable_detection['bbox'])
                if iou > best_iou and iou > self.config.IOU_THRESHOLD:
                    best_iou = iou
                    best_match = stable_id
            
            if best_match:
                # Mevcut tespitin güncelle (yumuşatma)
                old_detection = self.stable_detections[best_match]
                alpha = self.config.SMOOTHING_FACTOR  # Konfigürasyondan al
                
                # Bounding box yumuşatma
                new_bbox = [
                    int(alpha * bbox[0] + (1 - alpha) * old_detection['bbox'][0]),
                    int(alpha * bbox[1] + (1 - alpha) * old_detection['bbox'][1]),
                    int(alpha * bbox[2] + (1 - alpha) * old_detection['bbox'][2]),
                    int(alpha * bbox[3] + (1 - alpha) * old_detection['bbox'][3])
                ]
                
                # Güven skoru yumuşatma
                new_confidence = alpha * confidence + (1 - alpha) * old_detection['confidence']
                
                self.stable_detections[best_match] = {
                    'bbox': new_bbox,
                    'class_id': class_id,
                    'class_name': detection['class_name'],
                    'confidence': new_confidence,
                    'is_truck': detection['is_truck'],
                    'last_seen': time.time(),
                    'stability_count': old_detection.get('stability_count', 0) + 1
                }
                
                # Kararlı tespitleri ekle
                if old_detection.get('stability_count', 0) >= self.config.STABILITY_THRESHOLD:
                    smoothed_detections.append(self.stable_detections[best_match])
            else:
                # Yeni tespit
                self.detection_id_counter += 1
                self.stable_detections[self.detection_id_counter] = {
                    'bbox': bbox,
                    'class_id': class_id,
                    'class_name': detection['class_name'],
                    'confidence': confidence,
                    'is_truck': detection['is_truck'],
                    'last_seen': time.time(),
                    'stability_count': 1
                }
        
        # Eski tespitleri temizle
        current_time = time.time()
        to_remove = []
        for stable_id, stable_detection in self.stable_detections.items():
            if current_time - stable_detection['last_seen'] > self.config.DETECTION_TIMEOUT:
                to_remove.append(stable_id)
        
        for stable_id in to_remove:
            del self.stable_detections[stable_id]
        
        return smoothed_detections
    
    def detect_frame(self, frame, conf_threshold=None):
        """Gelişmiş frame tespiti - stabilizasyon ile"""
        
        # Frame atlama kontrolü
        self.frame_skip += 1
        if self.frame_skip % self.process_every_n_frames != 0:
            # Önceki kararlı tespitleri döndür
            return [det for det in self.stable_detections.values() 
                   if det.get('stability_count', 0) >= 3]
        
        if conf_threshold is None:
            conf_threshold = self.confidence_threshold
        
        detections = []
        
        try:
            if self.model is None:
                return self._fallback_detection_frame(frame)
            
            # Görüntü ön işleme
            processed_frame = self._preprocess_frame(frame)
            
            # YOLO ile tespit yap - gelişmiş parametreler
            model_params = self.config.get_model_params()
            model_params['conf'] = conf_threshold  # Override confidence
            
            results = self.model(
                processed_frame, 
                **model_params
            )
            
            # Sonuçları işle
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Sınıf ID'sini al
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        
                        # Araç sınıfı mı kontrol et
                        if class_id in self.vehicle_classes:
                            vehicle_type = self.vehicle_classes[class_id]
                            
                            # Bounding box koordinatları
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            
                            # Koordinat doğrulama
                            x1, y1, x2, y2 = max(0, int(x1)), max(0, int(y1)), int(x2), int(y2)
                            
                            detection = {
                                'class_id': class_id,
                                'class_name': vehicle_type,
                                'confidence': confidence,
                                'bbox': [x1, y1, x2, y2],
                                'is_truck': vehicle_type in self.truck_classes
                            }
                            
                            detections.append(detection)
            
            # Tespitleri yumuşat ve stabilize et
            smoothed_detections = self._smooth_detection(detections)
            
            # Geçmişe ekle
            self.detection_history.append(smoothed_detections)
            
            return smoothed_detections
            
        except Exception as e:
            logger.error(f"❌ Frame tespit hatası: {str(e)}")
            return []
    
    def _preprocess_frame(self, frame):
        """Frame ön işleme"""
        preprocessing_params = self.config.get_preprocessing_params()
        
        # Görüntü kalitesini artır
        processed = cv2.convertScaleAbs(frame, 
                                       alpha=preprocessing_params['alpha'], 
                                       beta=preprocessing_params['beta'])
        
        # Gürültü azaltma (eğer aktifse)
        if preprocessing_params['noise_reduction']:
            processed = cv2.bilateralFilter(processed, 9, 75, 75)
        
        return processed
    
    def draw_detections(self, frame, detections):
        """Gelişmiş tespit çizimi"""
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            class_name = detection['class_name']
            confidence = detection['confidence']
            is_truck = detection.get('is_truck', False)
            stability_count = detection.get('stability_count', 0)
            
            # Renk seç (kararlılığa göre)
            if stability_count >= 5:
                color = self.config.COLORS['truck_very_stable'] if is_truck else self.config.COLORS['very_stable']
            elif stability_count >= self.config.STABILITY_THRESHOLD:
                color = self.config.COLORS['truck_stable'] if is_truck else self.config.COLORS['stable']
            else:
                color = self.config.COLORS['unstable']
            
            # Kalınlık (kararlılığa göre)
            thickness = min(3 + stability_count // 2, 6)
            
            # Bounding box çiz
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            
            # Etiket hazırla
            label = f"{class_name}: {confidence:.2f}"
            if is_truck:
                label += " (KAMYON/TIR)"
            
            # Kararlılık göstergesi
            if stability_count >= self.config.STABILITY_THRESHOLD:
                label += f" ✓{stability_count}"
            
            # Etiket boyutunu hesapla
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            # Etiket arka planı
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            
            # Etiket yazısı
            cv2.putText(frame, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Stabilizasyon bilgisi
        stable_count = len([d for d in detections if d.get('stability_count', 0) >= self.config.STABILITY_THRESHOLD])
        info_text = f"Kararlı Tespit: {stable_count}/{len(detections)}"
        cv2.putText(frame, info_text, (10, frame.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def list_available_cameras(self, max_cameras=10):
        """Mevcut kameraları listele"""
        available_cameras = []
        
        print("🔍 Mevcut kameralar taranıyor...")
        
        for camera_id in range(max_cameras):
            cap = cv2.VideoCapture(camera_id)
            if cap.isOpened():
                # Kamera bilgilerini al
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                
                camera_info = {
                    'id': camera_id,
                    'name': f"Kamera {camera_id}",
                    'resolution': f"{width}x{height}",
                    'fps': fps
                }
                
                available_cameras.append(camera_info)
                print(f"✅ Kamera {camera_id}: {width}x{height} @ {fps}fps")
                cap.release()
            else:
                cap.release()
        
        if not available_cameras:
            print("❌ Hiç kamera bulunamadı!")
        
        return available_cameras
    
    def select_camera(self):
        """Kullanıcının kamera seçmesini sağla"""
        cameras = self.list_available_cameras()
        
        if not cameras:
            return None
        
        print("\n📹 Mevcut Kameralar:")
        print("-" * 50)
        for i, cam in enumerate(cameras):
            print(f"{i + 1}. {cam['name']} - {cam['resolution']} @ {cam['fps']}fps")
        
        print("-" * 50)
        
        while True:
            try:
                choice = input(f"Kamera seçin (1-{len(cameras)}) veya 'q' ile çıkış: ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(cameras):
                    selected_camera = cameras[choice_num - 1]
                    print(f"✅ Seçilen kamera: {selected_camera['name']}")
                    return selected_camera['id']
                else:
                    print(f"❌ Geçersiz seçim! 1-{len(cameras)} arası bir sayı girin.")
                    
            except ValueError:
                print("❌ Geçersiz giriş! Sayı girin.")
            except KeyboardInterrupt:
                print("\n🛑 İptal edildi.")
                return None
    
    def calculate_fps(self):
        """FPS hesapla"""
        self.fps_counter += 1
        current_time = time.time()
        elapsed_time = current_time - self.fps_start_time
        
        if elapsed_time >= 1.0:  # Her saniye güncelle
            fps = self.fps_counter / elapsed_time
            self.fps_counter = 0
            self.fps_start_time = current_time
            return round(fps, 1)
        
        return 0
    
    def run_camera(self, camera_id=None, window_name="Araç Kapısı - Araç Tespiti"):
        """Kameradan gerçek zamanlı tespit"""
        
        # Kamera seçimi
        if camera_id is None:
            camera_id = self.select_camera()
            if camera_id is None:
                print("❌ Kamera seçilmedi, çıkış yapılıyor.")
                return
        
        print(f"🎥 Kamera {camera_id} açılıyor...")
        cap = cv2.VideoCapture(camera_id)
        
        if not cap.isOpened():
            print(f"❌ Kamera {camera_id} açılamadı!")
            print("💡 Farklı bir kamera ID'si deneyin veya kamera bağlantısını kontrol edin.")
            return
        
        # Kamera ayarları
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Gerçek ayarları al
        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        print("✅ Kamera başlatıldı")
        print(f"📐 Çözünürlük: {actual_width}x{actual_height}")
        print(f"🎬 FPS: {actual_fps}")
        print("🎯 Araç tespiti başlıyor...")
        print("⌨️  Kontroller: 'q' = çıkış, 's' = ekran görüntüsü, 'p' = duraklat")
        
        frame_count = 0
        paused = False
        
        while True:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Frame okunamadı!")
                    break
                
                frame_count += 1
                
                # Her frame'i işleme (performans için ayarlanabilir)
                if frame_count % 1 == 0:  # Her frame işle
                    # Tespit yap
                    detections = self.detect_frame(frame, conf_threshold=0.4)
                    
                    # Sonuçları çiz
                    frame = self.draw_detections(frame, detections)
                    
                    # Bilgi metinleri
                    fps = self.calculate_fps()
                    info_text = f"FPS: {fps} | Tespit: {len(detections)} | Frame: {frame_count}"
                    cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Kamyon/tır tespiti varsa özel bildirim
                    truck_count = sum(1 for det in detections if det['is_truck'])
                    if truck_count > 0:
                        truck_text = f"KAMYON/TIR TESPIT EDILDI: {truck_count}"
                        cv2.putText(frame, truck_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 3)
                        
                        # Konsola da yazdır
                        if frame_count % 30 == 0:  # Her saniye bir yazdır
                            print(f"🚛 Frame {frame_count}: {truck_count} kamyon/tır tespit edildi!")
                            for det in detections:
                                if det['is_truck']:
                                    print(f"   - {det['class_name']}: {det['confidence']:.2f}")
                    
                    # Diğer araçları da göster
                    elif detections:
                        if frame_count % 60 == 0:  # 2 saniyede bir yazdır
                            print(f"🚗 Frame {frame_count}: {len(detections)} araç tespit edildi")
                            for det in detections:
                                print(f"   - {det['class_name']}: {det['confidence']:.2f}")
            
            # Duraklatma durumunda bilgi göster
            if paused:
                pause_text = "DURAKLADI - 'p' ile devam et"
                cv2.putText(frame, pause_text, (10, actual_height - 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            # Frame'i göster
            cv2.imshow(window_name, frame)
            
            # Klavye kontrolü
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("🛑 Çıkış yapılıyor...")
                break
            elif key == ord('s'):
                # Ekran görüntüsü kaydet
                timestamp = int(time.time())
                filename = f"arac_tespiti_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                print(f"📸 Ekran görüntüsü kaydedildi: {filename}")
            elif key == ord('p'):
                paused = not paused
                status = "durakladı" if paused else "devam ediyor"
                print(f"⏸️ Video {status}")
        
        # Temizlik
        cap.release()
        cv2.destroyAllWindows()
        print("✅ Kamera kapatıldı")
        print(f"📊 Toplam işlenen frame: {frame_count}")

    def detect(self, image):
        """
        Görüntüden araç tespiti yap (API için)
        
        Args:
            image: OpenCV formatında görüntü (BGR)
            
        Returns:
            dict: {
                'detected': bool,
                'type': str,
                'confidence': float,
                'bbox': list [x1, y1, x2, y2]
            }
        """
        try:
            if self.model is None:
                return self._fallback_detection(image)
            
            # YOLO ile tespit yap
            results = self.model(image, verbose=False)
            
            best_detection = {
                'detected': False,
                'type': 'unknown',
                'confidence': 0.0,
                'bbox': []
            }
            
            # Sonuçları işle
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Sınıf ID'sini al
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        
                        # Araç sınıfı mı kontrol et
                        if class_id in self.vehicle_classes and confidence > self.confidence_threshold:
                            vehicle_type = self.vehicle_classes[class_id]
                            
                            # En yüksek güvenilirlik skoruna sahip tespiti seç
                            if confidence > best_detection['confidence']:
                                # Bounding box koordinatları
                                x1, y1, x2, y2 = box.xyxy[0].tolist()
                                
                                best_detection = {
                                    'detected': True,
                                    'type': vehicle_type,
                                    'confidence': confidence,
                                    'bbox': [int(x1), int(y1), int(x2), int(y2)]
                                }
            
            # Kamyon/tır tespiti için tip kontrolü
            if best_detection['detected']:
                if best_detection['type'] in self.truck_classes:
                    best_detection['is_truck'] = True
                else:
                    best_detection['is_truck'] = False
                    
                logger.info(f"Araç tespit edildi: {best_detection['type']} (güven: {best_detection['confidence']:.2f})")
            else:
                logger.debug("Araç tespit edilmedi")
            
            return best_detection
            
        except Exception as e:
            logger.error(f"Araç tespit hatası: {str(e)}")
            return {
                'detected': False,
                'type': 'error',
                'confidence': 0.0,
                'bbox': []
            }
    
    def _fallback_detection_frame(self, frame):
        """Fallback frame tespiti"""
        try:
            height, width = frame.shape[:2]
            
            # Basit hareket tespiti veya renk bazlı tespit
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            detections = []
            
            # Büyük konturlar araç olabilir
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > (width * height * 0.05):  # Minimum alan
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Basit araç tipi tahmini
                    area_ratio = (w * h) / (width * height)
                    if area_ratio > 0.2:
                        vehicle_type = 'truck'
                        is_truck = True
                    else:
                        vehicle_type = 'car'
                        is_truck = False
                    
                    detection = {
                        'class_id': 7 if is_truck else 2,
                        'class_name': vehicle_type,
                        'confidence': 0.6,
                        'bbox': [x, y, x+w, y+h],
                        'is_truck': is_truck
                    }
                    
                    detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"Fallback tespit hatası: {str(e)}")
            return []
    
    def _fallback_detection(self, image):
        """
        Model yüklenemediğinde basit araç tespiti
        (Gerçek projede daha gelişmiş yöntemler kullanılabilir)
        """
        try:
            # Basit hareket tespiti veya renk bazlı tespit
            # Bu örnekte rastgele bir sonuç döndürüyoruz
            height, width = image.shape[:2]
            
            # Görüntüde büyük nesneler var mı basit kontrol
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Büyük konturlar araç olabilir
            large_contours = [c for c in contours if cv2.contourArea(c) > (width * height * 0.1)]
            
            if large_contours:
                # En büyük konturu al
                largest_contour = max(large_contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                # Basit araç tipi tahmini (boyut bazlı)
                area_ratio = (w * h) / (width * height)
                if area_ratio > 0.3:
                    vehicle_type = 'truck'  # Büyük nesne = kamyon
                else:
                    vehicle_type = 'car'
                
                return {
                    'detected': True,
                    'type': vehicle_type,
                    'confidence': 0.7,  # Sabit güven skoru
                    'bbox': [x, y, x+w, y+h],
                    'is_truck': vehicle_type == 'truck'
                }
            
            return {
                'detected': False,
                'type': 'none',
                'confidence': 0.0,
                'bbox': []
            }
            
        except Exception as e:
            logger.error(f"Fallback tespit hatası: {str(e)}")
            return {
                'detected': False,
                'type': 'error',
                'confidence': 0.0,
                'bbox': []
            }
    
    def draw_detection(self, image, detection):
        """
        Tespit sonucunu görüntü üzerine çiz
        """
        if not detection['detected'] or not detection['bbox']:
            return image
        
        try:
            x1, y1, x2, y2 = detection['bbox']
            
            # Bounding box çiz
            color = (0, 255, 0) if detection.get('is_truck', False) else (255, 0, 0)
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            
            # Etiket yazısı
            label = f"{detection['type']} ({detection['confidence']:.2f})"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            # Etiket arka planı
            cv2.rectangle(image, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            
            # Etiket yazısı
            cv2.putText(image, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            return image
            
        except Exception as e:
            logger.error(f"Çizim hatası: {str(e)}")
            return image 