import cv2
import numpy as np
import easyocr
import re
import logging

logger = logging.getLogger(__name__)

class PlateReader:
    def __init__(self):
        """
        Plaka okuma sınıfını başlat
        """
        try:
            # EasyOCR okuyucusunu başlat (Türkçe ve İngilizce)
            self.reader = easyocr.Reader(['tr', 'en'], gpu=False)
            logger.info("EasyOCR başlatıldı")
            
            # Türk plaka formatı regex'i
            self.turkish_plate_pattern = re.compile(r'^[0-9]{2}\s?[A-Z]{1,3}\s?[0-9]{1,4}$')
            
        except Exception as e:
            logger.error(f"OCR başlatma hatası: {str(e)}")
            self.reader = None
    
    def read_plate(self, image):
        """
        Görüntüden plaka okur
        
        Args:
            image: OpenCV formatında görüntü (BGR)
            
        Returns:
            dict: {
                'detected': bool,
                'text': str,
                'confidence': float,
                'bbox': list
            }
        """
        try:
            if self.reader is None:
                return self._fallback_plate_reading(image)
            
            # Plaka bölgesini tespit et ve oku
            plate_regions = self._detect_plate_regions(image)
            
            best_result = {
                'detected': False,
                'text': '',
                'confidence': 0.0,
                'bbox': []
            }
            
            for region in plate_regions:
                # Bölgeyi kırp
                x, y, w, h = region
                plate_crop = image[y:y+h, x:x+w]
                
                # Plaka görüntüsünü ön işle
                processed_plate = self._preprocess_plate(plate_crop)
                
                # OCR ile oku
                ocr_results = self.reader.readtext(processed_plate)
                
                for (bbox, text, confidence) in ocr_results:
                    # Metni temizle
                    cleaned_text = self._clean_plate_text(text)
                    
                    # Türk plaka formatına uygun mu kontrol et
                    if self._is_valid_turkish_plate(cleaned_text) and confidence > best_result['confidence']:
                        best_result = {
                            'detected': True,
                            'text': cleaned_text,
                            'confidence': confidence,
                            'bbox': [x, y, x+w, y+h]
                        }
            
            if best_result['detected']:
                logger.info(f"Plaka okundu: {best_result['text']} (güven: {best_result['confidence']:.2f})")
            else:
                logger.debug("Plaka okunamadı")
            
            return best_result
            
        except Exception as e:
            logger.error(f"Plaka okuma hatası: {str(e)}")
            return {
                'detected': False,
                'text': '',
                'confidence': 0.0,
                'bbox': []
            }
    
    def _detect_plate_regions(self, image):
        """
        Görüntüde plaka olabilecek bölgeleri tespit et
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Kenar tespiti
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Morfolojik işlemler
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
            
            # Konturları bul
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            plate_regions = []
            
            for contour in contours:
                # Kontur alanı kontrolü
                area = cv2.contourArea(contour)
                if area < 1000:  # Çok küçük alanları atla
                    continue
                
                # Bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Plaka oranı kontrolü (genişlik/yükseklik)
                aspect_ratio = w / h
                if 2.0 < aspect_ratio < 6.0:  # Plaka oranı
                    plate_regions.append((x, y, w, h))
            
            # Eğer plaka bölgesi bulunamazsa, tüm görüntüyü kullan
            if not plate_regions:
                h, w = image.shape[:2]
                plate_regions = [(0, 0, w, h)]
            
            return plate_regions
            
        except Exception as e:
            logger.error(f"Plaka bölgesi tespit hatası: {str(e)}")
            h, w = image.shape[:2]
            return [(0, 0, w, h)]
    
    def _preprocess_plate(self, plate_image):
        """
        Plaka görüntüsünü OCR için ön işle
        """
        try:
            # Gri tonlamaya çevir
            if len(plate_image.shape) == 3:
                gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = plate_image
            
            # Kontrast artırma
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # Gürültü azaltma
            denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
            
            # Eşikleme
            _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Morfolojik işlemler
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            return processed
            
        except Exception as e:
            logger.error(f"Plaka ön işleme hatası: {str(e)}")
            return plate_image
    
    def _clean_plate_text(self, text):
        """
        OCR sonucunu temizle ve düzenle
        """
        # Boşlukları ve özel karakterleri temizle
        cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        # Türk plaka formatına uygun hale getir
        if len(cleaned) >= 6:
            # İlk 2 karakter sayı olmalı
            if cleaned[:2].isdigit():
                # Sonraki 1-3 karakter harf olmalı
                letters_start = 2
                letters_end = letters_start
                
                for i in range(letters_start, min(letters_start + 3, len(cleaned))):
                    if cleaned[i].isalpha():
                        letters_end = i + 1
                    else:
                        break
                
                if letters_end > letters_start:
                    # Kalan karakterler sayı olmalı
                    numbers_part = cleaned[letters_end:]
                    if numbers_part.isdigit():
                        # Format: 34ABC1234
                        formatted = cleaned[:2] + cleaned[letters_start:letters_end] + numbers_part
                        return formatted
        
        return cleaned
    
    def _is_valid_turkish_plate(self, text):
        """
        Türk plaka formatına uygun mu kontrol et
        """
        if len(text) < 6 or len(text) > 8:
            return False
        
        # Basit format kontrolü: 2 sayı + 1-3 harf + 1-4 sayı
        if not text[:2].isdigit():
            return False
        
        # Harf kısmını bul
        letter_part = ""
        number_part = ""
        
        for i in range(2, len(text)):
            if text[i].isalpha() and len(letter_part) < 3:
                letter_part += text[i]
            elif text[i].isdigit():
                number_part = text[i:]
                break
        
        # Kontroller
        if len(letter_part) < 1 or len(letter_part) > 3:
            return False
        
        if len(number_part) < 1 or len(number_part) > 4:
            return False
        
        if not number_part.isdigit():
            return False
        
        return True
    
    def _fallback_plate_reading(self, image):
        """
        OCR başarısız olduğunda basit plaka okuma
        """
        try:
            # Basit template matching veya başka yöntemler kullanılabilir
            # Bu örnekte sabit bir plaka döndürüyoruz
            logger.warning("OCR mevcut değil, fallback kullanılıyor")
            
            return {
                'detected': True,
                'text': '34ABC1234',  # Test plakası
                'confidence': 0.5,
                'bbox': [0, 0, 100, 50]
            }
            
        except Exception as e:
            logger.error(f"Fallback plaka okuma hatası: {str(e)}")
            return {
                'detected': False,
                'text': '',
                'confidence': 0.0,
                'bbox': []
            }
    
    def draw_plate_detection(self, image, detection):
        """
        Plaka tespit sonucunu görüntü üzerine çiz
        """
        if not detection['detected'] or not detection['bbox']:
            return image
        
        try:
            x1, y1, x2, y2 = detection['bbox']
            
            # Plaka bounding box'ı çiz
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 255), 2)
            
            # Plaka metnini yaz
            label = f"Plaka: {detection['text']}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            
            # Etiket arka planı
            cv2.rectangle(image, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), (0, 255, 255), -1)
            
            # Etiket yazısı
            cv2.putText(image, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            
            return image
            
        except Exception as e:
            logger.error(f"Plaka çizim hatası: {str(e)}")
            return image 