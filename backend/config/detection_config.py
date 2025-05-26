"""
Real-Time Detection Konfigürasyon Ayarları
"""

class DetectionConfig:
    """Tespit parametreleri"""
    
    # Model Ayarları
    CONFIDENCE_THRESHOLD = 0.6  # Güven eşiği (0.5-0.8 arası önerilen)
    NMS_THRESHOLD = 0.4  # Non-Maximum Suppression eşiği
    MAX_DETECTIONS = 10  # Maksimum tespit sayısı
    MIN_DETECTION_AREA = 2000  # Minimum tespit alanı (piksel)
    
    # Stabilizasyon Ayarları
    STABILITY_THRESHOLD = 3  # Kararlı tespit için minimum frame sayısı
    SMOOTHING_FACTOR = 0.7  # Bounding box yumuşatma faktörü (0.5-0.9)
    IOU_THRESHOLD = 0.3  # Overlap eşiği
    DETECTION_TIMEOUT = 2.0  # Tespit timeout süresi (saniye)
    
    # Frame İşleme
    PROCESS_EVERY_N_FRAMES = 2  # Her N frame'de bir işle
    HISTORY_SIZE = 10  # Geçmiş frame sayısı
    
    # Görüntü İyileştirme
    CONTRAST_ALPHA = 1.1  # Kontrast çarpanı
    BRIGHTNESS_BETA = 10  # Parlaklık ekleme
    NOISE_REDUCTION = True  # Gürültü azaltma
    
    # Kamera Ayarları
    CAMERA_WIDTH = 1280
    CAMERA_HEIGHT = 720
    CAMERA_FPS = 30
    
    # Renk Kodları (BGR)
    COLORS = {
        'very_stable': (0, 255, 0),    # Yeşil - Çok kararlı
        'stable': (0, 200, 0),         # Koyu yeşil - Kararlı
        'unstable': (0, 150, 150),     # Gri - Kararsız
        'truck_very_stable': (0, 255, 255),  # Sarı - Kamyon çok kararlı
        'truck_stable': (0, 200, 200),       # Koyu sarı - Kamyon kararlı
    }
    
    # Performans Ayarları
    ENABLE_GPU = True  # GPU kullanımı
    ENABLE_HALF_PRECISION = False  # Yarı hassasiyet (FP16)
    
    @classmethod
    def get_model_params(cls):
        """Model parametrelerini döndür"""
        return {
            'conf': cls.CONFIDENCE_THRESHOLD,
            'iou': cls.NMS_THRESHOLD,
            'max_det': cls.MAX_DETECTIONS,
            'agnostic_nms': True,
            'verbose': False
        }
    
    @classmethod
    def get_preprocessing_params(cls):
        """Ön işleme parametrelerini döndür"""
        return {
            'alpha': cls.CONTRAST_ALPHA,
            'beta': cls.BRIGHTNESS_BETA,
            'noise_reduction': cls.NOISE_REDUCTION
        }
    
    @classmethod
    def get_stabilization_params(cls):
        """Stabilizasyon parametrelerini döndür"""
        return {
            'stability_threshold': cls.STABILITY_THRESHOLD,
            'smoothing_factor': cls.SMOOTHING_FACTOR,
            'iou_threshold': cls.IOU_THRESHOLD,
            'timeout': cls.DETECTION_TIMEOUT
        } 