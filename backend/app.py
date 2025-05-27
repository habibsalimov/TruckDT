from flask import Flask, request, jsonify, Response # type: ignore
from flask_cors import CORS # type: ignore
import cv2 # type: ignore
import numpy as np # type: ignore
import base64
import io
from PIL import Image # type: ignore
import os
from dotenv import load_dotenv # type: ignore
import logging
import traceback
from datetime import datetime
import time
import threading

# Kendi modüllerimizi import ediyoruz
from utils.vehicle_detector import VehicleDetector
from utils.plate_reader import PlateReader
from database_utils.database import SupabaseDB

# Environment variables yükle
load_dotenv()

# Flask uygulamasını oluştur
app = Flask(__name__)
CORS(app)  # React frontend ile iletişim için

# Global kamera değişkenleri
camera = None
camera_id = 1  # Varsayılan olarak kamera 1
camera_active = False
detection_active = False

# Son tespit sonucu için global değişken
last_detection_result = None

# Gelişmiş logging ayarla
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Başlangıç logları
logger.info("🚛 Araç Kapısı & Plaka Tespit Sistemi başlatılıyor...")
logger.info(f"Python sürümü: {os.sys.version}")
logger.info(f"Çalışma dizini: {os.getcwd()}")

# Sınıfları başlat
try:
    logger.info("VehicleDetector başlatılıyor...")
    detector = VehicleDetector()
    logger.info("✅ VehicleDetector başarıyla başlatıldı")
except Exception as e:
    logger.error(f"❌ VehicleDetector başlatma hatası: {str(e)}")
    logger.error(traceback.format_exc())

try:
    logger.info("PlateReader başlatılıyor...")
    plate_reader = PlateReader()
    logger.info("✅ PlateReader başarıyla başlatıldı")
except Exception as e:
    logger.error(f"❌ PlateReader başlatma hatası: {str(e)}")
    logger.error(traceback.format_exc())

try:
    logger.info("SupabaseDB bağlantısı kuruluyor...")
    supabase_db = SupabaseDB()
    logger.info("✅ SupabaseDB başarıyla bağlandı")
    
    # Demo plakaları kur
    try:
        supabase_db.setup_demo_plates()
    except Exception as demo_error:
        logger.warning(f"⚠️ Demo plaka kurulumu başarısız: {str(demo_error)}")
        
except Exception as e:
    logger.error(f"❌ SupabaseDB bağlantı hatası: {str(e)}")
    logger.error(traceback.format_exc())
    supabase_db = None

def init_camera(cam_id=1):
    """Kamerayı başlat"""
    global camera, camera_id, camera_active
    
    try:
        if camera is not None:
            camera.release()
        
        logger.info(f"🎥 Kamera {cam_id} başlatılıyor...")
        camera = cv2.VideoCapture(cam_id)
        
        if not camera.isOpened():
            logger.error(f"❌ Kamera {cam_id} açılamadı!")
            return False
        
        # Kamera ayarları
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        camera.set(cv2.CAP_PROP_FPS, 30)
        
        camera_id = cam_id
        camera_active = True
        
        # Gerçek ayarları al
        width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(camera.get(cv2.CAP_PROP_FPS))
        
        logger.info(f"✅ Kamera {cam_id} başlatıldı: {width}x{height} @ {fps}fps")
        return True
        
    except Exception as e:
        logger.error(f"❌ Kamera başlatma hatası: {str(e)}")
        camera_active = False
        return False

def generate_frames():
    """Video stream için frame üret"""
    global camera, detection_active
    
    if camera is None:
        return
    
    frame_count = 0
    fps_start_time = time.time()
    last_detection_time = 0  # Son tespit zamanı
    detection_cooldown = 3.0  # 3 saniye bekleme süresi
    
    while camera_active:
        try:
            success, frame = camera.read()
            if not success:
                logger.error("Kameradan frame okunamadı")
                break
            
            frame_count += 1
            current_time = time.time()
            
            # Tespit aktif ise araç tespiti yap
            if detection_active:
                detections = detector.detect_frame(frame)
                frame = detector.draw_detections(frame, detections)
                
                # Kararlı kamyon tespiti varsa işle
                stable_trucks = [d for d in detections if d.get('is_truck', False) and d.get('stability_count', 0) >= 3]
                
                # Cooldown kontrolü - çok sık tespit yapmayı önle
                if stable_trucks and (current_time - last_detection_time) > detection_cooldown:
                    logger.info(f"🚛 {len(stable_trucks)} adet kararlı kamyon/tır tespit edildi!")
                    
                    for truck in stable_trucks:
                        try:
                            # Plaka tespiti için ROI al
                            x1, y1, x2, y2 = truck['bbox']
                            
                            # ROI boyut kontrolü
                            if x2 > x1 and y2 > y1:
                                roi = frame[y1:y2, x1:x2]
                                
                                # ROI boyutu yeterli mi kontrol et
                                if roi.shape[0] > 50 and roi.shape[1] > 50:
                                    # Plaka tespit et
                                    plate_result = plate_reader.read_plate(roi)
                                    
                                    if plate_result.get('detected', False) and plate_result.get('text'):
                                        plate_text = plate_result['text'].strip().upper()
                                        
                                        if len(plate_text) >= 5:  # Minimum plaka uzunluğu
                                            logger.info(f"📋 Plaka okundu: {plate_text}")
                                            
                                            # Veritabanında kontrol et
                                            if supabase_db:
                                                try:
                                                    is_authorized = supabase_db.check_plate(plate_text)
                                                    
                                                    # Erişim logunu kaydet
                                                    access_granted = is_authorized
                                                    gate_action = 'open' if is_authorized else 'denied'
                                                    
                                                    supabase_db.add_access_log(
                                                        plate_text,
                                                        truck['class_name'],
                                                        gate_action,
                                                        access_granted
                                                    )
                                                    
                                                    if is_authorized:
                                                        logger.info(f"✅ Erişim izni verildi: {plate_text}")
                                                        # Frame'e başarı mesajı ekle
                                                        cv2.putText(frame, f"ERISIM IZNI VERILDI: {plate_text}", 
                                                                   (10, frame.shape[0] - 60), 
                                                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                                                    else:
                                                        logger.warning(f"❌ Erişim reddedildi: {plate_text}")
                                                        # Frame'e ret mesajı ekle
                                                        cv2.putText(frame, f"ERISIM REDDEDILDI: {plate_text}", 
                                                                   (10, frame.shape[0] - 60), 
                                                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                                                    
                                                    # Son tespit sonucunu global değişkene kaydet
                                                    global last_detection_result
                                                    last_detection_result = {
                                                        'plate_text': plate_text,
                                                        'vehicle_type': truck['class_name'],
                                                        'gate_action': gate_action,
                                                        'is_authorized': is_authorized,
                                                        'timestamp': datetime.now().isoformat(),
                                                        'access_granted': access_granted
                                                    }
                                                    
                                                    # Son tespit zamanını güncelle
                                                    last_detection_time = current_time
                                                    
                                                except Exception as db_error:
                                                    logger.error(f"Veritabanı işlem hatası: {str(db_error)}")
                                            else:
                                                logger.warning("Supabase bağlantısı yok, plaka kontrol edilemiyor")
                                        else:
                                            logger.debug(f"Plaka çok kısa: {plate_text}")
                                    else:
                                        logger.debug("Plaka okunamadı veya boş")
                                else:
                                    logger.debug("ROI boyutu çok küçük")
                            else:
                                logger.debug("Geçersiz bounding box koordinatları")
                                
                        except Exception as e:
                            logger.error(f"Plaka işleme hatası: {str(e)}")
                
                # Genel tespit bilgisini frame'e ekle
                if detections:
                    total_vehicles = len(detections)
                    stable_vehicles = len([d for d in detections if d.get('stability_count', 0) >= 3])
                    
                    info_text = f"Arac: {total_vehicles} | Kararli: {stable_vehicles}"
                    cv2.putText(frame, info_text, (10, frame.shape[0] - 100), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # FPS hesapla ve göster
            if frame_count % 30 == 0:  # Her 30 frame'de bir
                elapsed = current_time - fps_start_time
                fps = 30 / elapsed if elapsed > 0 else 0
                
                # FPS bilgisini frame'e ekle
                cv2.putText(frame, f"FPS: {fps:.1f}", (frame.shape[1] - 120, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                fps_start_time = current_time
            
            # Tespit durumu göstergesi
            status_text = "GERCEK ZAMANLI TESPIT AKTIF" if detection_active else "TESPIT PASIF"
            status_color = (0, 255, 0) if detection_active else (0, 0, 255)
            cv2.putText(frame, status_text, (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            
            # Frame'i encode et
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()
            
            # Multipart response
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
        except Exception as e:
            logger.error(f"Frame üretim hatası: {str(e)}")
            break

@app.route('/api/health', methods=['GET'])
def health_check():
    """API sağlık kontrolü"""
    logger.info("Sağlık kontrolü istendi")
    
    health_status = {
        'status': 'healthy',
        'message': 'Araç Kapısı API çalışıyor',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'vehicle_detector': 'ok' if 'detector' in globals() else 'error',
            'plate_reader': 'ok' if 'plate_reader' in globals() else 'error',
            'supabase_db': 'ok' if supabase_db is not None else 'error',
            'camera': 'active' if camera_active else 'inactive'
        },
        'camera_info': {
            'id': camera_id,
            'active': camera_active,
            'detection_active': detection_active
        }
    }
    
    logger.info(f"Sağlık durumu: {health_status}")
    return jsonify(health_status)

@app.route('/api/camera/list', methods=['GET'])
def list_cameras():
    """Mevcut kameraları listele"""
    logger.info("📹 Kamera listesi istendi")
    
    try:
        cameras = detector.list_available_cameras()
        return jsonify({
            'cameras': cameras,
            'current_camera': camera_id,
            'camera_active': camera_active
        })
    except Exception as e:
        logger.error(f"❌ Kamera listeleme hatası: {str(e)}")
        return jsonify({'error': 'Kamera listeleme başarısız'}), 500

@app.route('/api/camera/start', methods=['POST'])
def start_camera():
    """Kamerayı başlat"""
    logger.info("🎥 Kamera başlatma isteği")
    
    try:
        data = request.get_json()
        cam_id = data.get('camera_id', 1)
        
        if init_camera(cam_id):
            return jsonify({
                'success': True,
                'message': f'Kamera {cam_id} başlatıldı',
                'camera_id': cam_id
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Kamera {cam_id} başlatılamadı'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Kamera başlatma hatası: {str(e)}")
        return jsonify({'error': 'Kamera başlatma başarısız'}), 500

@app.route('/api/camera/stop', methods=['POST'])
def stop_camera():
    """Kamerayı durdur"""
    global camera, camera_active, detection_active
    
    logger.info("🛑 Kamera durdurma isteği")
    
    try:
        camera_active = False
        detection_active = False
        
        if camera is not None:
            camera.release()
            camera = None
        
        return jsonify({
            'success': True,
            'message': 'Kamera durduruldu'
        })
        
    except Exception as e:
        logger.error(f"❌ Kamera durdurma hatası: {str(e)}")
        return jsonify({'error': 'Kamera durdurma başarısız'}), 500

@app.route('/api/camera/stream')
def camera_stream():
    """Kamera stream endpoint'i"""
    global camera_active
    
    if not camera_active:
        # Kamera aktif değilse başlat
        if not init_camera(camera_id):
            return "Kamera başlatılamadı", 500
    
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/detection/start', methods=['POST'])
def start_detection():
    """Gerçek zamanlı tespiti başlat"""
    global detection_active
    
    logger.info("🎯 Gerçek zamanlı tespit başlatılıyor")
    
    try:
        if not camera_active:
            return jsonify({
                'success': False,
                'message': 'Önce kamerayı başlatın'
            }), 400
        
        detection_active = True
        
        return jsonify({
            'success': True,
            'message': 'Gerçek zamanlı tespit başlatıldı'
        })
        
    except Exception as e:
        logger.error(f"❌ Tespit başlatma hatası: {str(e)}")
        return jsonify({'error': 'Tespit başlatma başarısız'}), 500

@app.route('/api/detection/stop', methods=['POST'])
def stop_detection():
    """Gerçek zamanlı tespiti durdur"""
    global detection_active
    
    logger.info("🛑 Gerçek zamanlı tespit durdurma isteği")
    
    try:
        detection_active = False
        
        return jsonify({
            'success': True,
            'message': 'Gerçek zamanlı tespit durduruldu'
        })
        
    except Exception as e:
        logger.error(f"❌ Tespit durdurma hatası: {str(e)}")
        return jsonify({'error': 'Tespit durdurma başarısız'}), 500

@app.route('/api/detection/latest', methods=['GET'])
def get_latest_detection():
    """En son tespit sonucunu döndür"""
    global last_detection_result
    
    if last_detection_result is None:
        return jsonify({
            'has_result': False,
            'message': 'Henüz tespit yapılmadı'
        })
    
    # Sonucu döndür ve sıfırla (bir kez göster)
    result = last_detection_result.copy()
    last_detection_result = None
    
    return jsonify({
        'has_result': True,
        'result': result
    })

@app.route('/api/plates', methods=['GET'])
def get_plates():
    """Kayıtlı plakaları getir"""
    logger.info("📋 Plaka listesi istendi")
    
    try:
        if not supabase_db:
            logger.error("❌ Supabase bağlantısı yok")
            return jsonify({'error': 'Veritabanı bağlantısı yok'}), 500
            
        plates = supabase_db.get_all_plates()
        logger.info(f"📋 {len(plates)} plaka bulundu")
        return jsonify({'plates': plates})
    except Exception as e:
        logger.error(f"❌ Plaka getirme hatası: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Plakalar getirilemedi', 'details': str(e)}), 500

@app.route('/api/plates', methods=['POST'])
def add_plate():
    """Yeni plaka ekle"""
    logger.info("➕ Yeni plaka ekleme isteği")
    
    try:
        if not supabase_db:
            logger.error("❌ Supabase bağlantısı yok")
            return jsonify({'error': 'Veritabanı bağlantısı yok'}), 500
            
        data = request.get_json()
        logger.info(f"📥 Gelen veri: {data}")
        
        if 'plate_number' not in data:
            logger.error("❌ Plaka numarası eksik")
            return jsonify({'error': 'Plaka numarası gerekli'}), 400
        
        plate_number = data['plate_number'].upper().strip()
        logger.info(f"🔤 İşlenmiş plaka: {plate_number}")
        
        # Plaka formatını kontrol et (basit kontrol)
        if len(plate_number) < 5:
            logger.error(f"❌ Geçersiz plaka formatı: {plate_number}")
            return jsonify({'error': 'Geçersiz plaka formatı'}), 400
        
        logger.info(f"💾 Plaka veritabanına ekleniyor: {plate_number}")
        result = supabase_db.add_plate(plate_number)
        
        if result:
            logger.info(f"✅ Plaka başarıyla eklendi: {plate_number}")
            return jsonify({
                'success': True,
                'message': f'Plaka {plate_number} başarıyla eklendi'
            })
        else:
            logger.error(f"❌ Plaka eklenemedi: {plate_number}")
            return jsonify({'error': 'Plaka eklenemedi (muhtemelen zaten mevcut)'}), 400
            
    except Exception as e:
        logger.error(f"❌ Plaka ekleme hatası: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Plaka ekleme başarısız', 'details': str(e)}), 500

@app.route('/api/plates/<plate_id>', methods=['DELETE'])
def delete_plate(plate_id):
    """Plaka sil"""
    logger.info(f"🗑️ Plaka silme isteği: {plate_id}")
    
    try:
        if not supabase_db:
            logger.error("❌ Supabase bağlantısı yok")
            return jsonify({'error': 'Veritabanı bağlantısı yok'}), 500
            
        result = supabase_db.delete_plate(plate_id)
        
        if result:
            logger.info(f"✅ Plaka başarıyla silindi: {plate_id}")
            return jsonify({
                'success': True,
                'message': 'Plaka başarıyla silindi'
            })
        else:
            logger.error(f"❌ Plaka silinemedi: {plate_id}")
            return jsonify({'error': 'Plaka silinemedi'}), 500
            
    except Exception as e:
        logger.error(f"❌ Plaka silme hatası: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Plaka silme başarısız', 'details': str(e)}), 500

@app.route('/api/check-plate', methods=['POST'])
def check_plate():
    """Plaka kontrolü yap"""
    logger.info("🔍 Plaka kontrol isteği")
    
    try:
        if not supabase_db:
            logger.error("❌ Supabase bağlantısı yok")
            return jsonify({'error': 'Veritabanı bağlantısı yok'}), 500
            
        data = request.get_json()
        if 'plate_number' not in data:
            logger.error("❌ Plaka numarası eksik")
            return jsonify({'error': 'Plaka numarası gerekli'}), 400
        
        plate_number = data['plate_number'].upper().strip()
        logger.info(f"🔍 Kontrol edilen plaka: {plate_number}")
        
        is_authorized = supabase_db.check_plate(plate_number)
        logger.info(f"🔐 Plaka yetki durumu: {is_authorized}")
        
        return jsonify({
            'plate_number': plate_number,
            'authorized': is_authorized,
            'gate_action': 'open' if is_authorized else 'denied',
            'message': 'Yetkili araç' if is_authorized else 'Yetkisiz araç'
        })
        
    except Exception as e:
        logger.error(f"❌ Plaka kontrol hatası: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Plaka kontrolü başarısız', 'details': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Flask sunucusu başlatılıyor...")
    logger.info("📍 Backend: http://localhost:5001")
    logger.info("📍 Frontend: http://localhost:3000")
    logger.info("📍 API Docs: http://localhost:5001/api/health")
    
    # Geliştirme modunda çalıştır
    app.run(debug=True, host='0.0.0.0', port=5001) 