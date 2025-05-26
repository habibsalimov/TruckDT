import os
from supabase import create_client, Client
import logging
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

class SupabaseDB:
    def __init__(self):
        """Supabase bağlantısını başlat"""
        logger.info("🔗 Supabase bağlantısı kuruluyor...")
        
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        
        logger.info(f"📍 Supabase URL: {self.url}")
        logger.info(f"🔑 Supabase KEY: {'*' * 20 if self.key else 'YOK'}")
        
        if not self.url or not self.key:
            logger.error("❌ Supabase URL veya KEY bulunamadı!")
            logger.error("💡 .env dosyasını kontrol edin:")
            logger.error("   SUPABASE_URL=https://your-project.supabase.co")
            logger.error("   SUPABASE_KEY=your-anon-key-here")
            raise ValueError("Supabase yapılandırması eksik")
        
        try:
            self.supabase: Client = create_client(self.url, self.key)
            logger.info("✅ Supabase client başarıyla oluşturuldu")
            
            # Bağlantıyı test et
            self._test_connection()
            
        except Exception as e:
            logger.error(f"❌ Supabase bağlantı hatası: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def _test_connection(self):
        """Supabase bağlantısını test et"""
        try:
            logger.info("🧪 Supabase bağlantısı test ediliyor...")
            
            # Basit bir sorgu ile bağlantıyı test et
            response = self.supabase.table('plates').select('count').execute()
            logger.info("✅ Supabase bağlantı testi başarılı")
            
        except Exception as e:
            logger.warning(f"⚠️ Supabase bağlantı testi başarısız: {str(e)}")
            logger.warning("💡 Tablolar henüz oluşturulmamış olabilir")
    
    def get_all_plates(self):
        """Tüm kayıtlı plakaları getir"""
        try:
            logger.info("📋 Tüm plakalar getiriliyor...")
            response = self.supabase.table('plates').select('*').order('created_at', desc=True).execute()
            
            plates = response.data if response.data else []
            logger.info(f"📋 {len(plates)} plaka bulundu")
            
            for plate in plates:
                logger.debug(f"   - {plate.get('plate_number', 'N/A')} ({plate.get('created_at', 'N/A')})")
            
            return plates
            
        except Exception as e:
            logger.error(f"❌ Plaka getirme hatası: {str(e)}")
            logger.error(traceback.format_exc())
            return []
    
    def add_plate(self, plate_number):
        """Yeni plaka ekle"""
        try:
            logger.info(f"➕ Plaka ekleniyor: {plate_number}")
            
            # Önce aynı plaka var mı kontrol et
            logger.info(f"🔍 Mevcut plaka kontrolü: {plate_number}")
            existing = self.supabase.table('plates').select('*').eq('plate_number', plate_number).execute()
            
            if existing.data:
                logger.warning(f"⚠️ Plaka zaten mevcut: {plate_number}")
                logger.info(f"📋 Mevcut plaka bilgisi: {existing.data[0]}")
                return False
            
            # Yeni plaka ekle
            data = {
                'plate_number': plate_number,
                'created_at': datetime.now().isoformat()
            }
            
            logger.info(f"💾 Veritabanına ekleniyor: {data}")
            response = self.supabase.table('plates').insert(data).execute()
            
            if response.data:
                logger.info(f"✅ Plaka başarıyla eklendi: {plate_number}")
                logger.debug(f"📋 Eklenen veri: {response.data[0]}")
                return True
            else:
                logger.error(f"❌ Plaka eklenemedi: {plate_number}")
                logger.error(f"📋 Supabase yanıtı: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Plaka ekleme hatası: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def delete_plate(self, plate_id):
        """Plaka sil"""
        try:
            logger.info(f"🗑️ Plaka siliniyor: {plate_id}")
            
            # Önce plaka var mı kontrol et
            existing = self.supabase.table('plates').select('*').eq('id', plate_id).execute()
            
            if not existing.data:
                logger.warning(f"⚠️ Silinecek plaka bulunamadı: {plate_id}")
                return False
            
            plate_info = existing.data[0]
            logger.info(f"📋 Silinecek plaka: {plate_info.get('plate_number', 'N/A')}")
            
            response = self.supabase.table('plates').delete().eq('id', plate_id).execute()
            
            if response.data:
                logger.info(f"✅ Plaka başarıyla silindi: {plate_id}")
                return True
            else:
                logger.error(f"❌ Plaka silinemedi: {plate_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Plaka silme hatası: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def check_plate(self, plate_number):
        """Plaka veritabanında var mı kontrol et"""
        try:
            logger.info(f"🔍 Plaka kontrol ediliyor: {plate_number}")
            
            response = self.supabase.table('plates').select('*').eq('plate_number', plate_number).execute()
            
            is_authorized = len(response.data) > 0 if response.data else False
            
            if is_authorized:
                logger.info(f"✅ Yetkili plaka bulundu: {plate_number}")
                logger.debug(f"📋 Plaka bilgisi: {response.data[0]}")
            else:
                logger.warning(f"❌ Yetkisiz plaka: {plate_number}")
            
            return is_authorized
            
        except Exception as e:
            logger.error(f"❌ Plaka kontrol hatası: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def add_access_log(self, plate_number, vehicle_type, action, success=True):
        """Erişim logunu kaydet"""
        try:
            logger.info(f"📝 Erişim logu kaydediliyor: {plate_number} - {action}")
            
            data = {
                'plate_number': plate_number,
                'vehicle_type': vehicle_type,
                'action': action,  # 'open', 'denied'
                'success': success,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.debug(f"📋 Log verisi: {data}")
            response = self.supabase.table('access_logs').insert(data).execute()
            
            if response.data:
                logger.info(f"✅ Erişim logu kaydedildi: {plate_number} - {action}")
                return True
            else:
                logger.error(f"❌ Erişim logu kaydedilemedi: {plate_number}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erişim logu kaydetme hatası: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def get_access_logs(self, limit=100):
        """Erişim loglarını getir"""
        try:
            logger.info(f"📋 Son {limit} erişim logu getiriliyor...")
            
            response = self.supabase.table('access_logs').select('*').order('timestamp', desc=True).limit(limit).execute()
            
            logs = response.data if response.data else []
            logger.info(f"📋 {len(logs)} erişim logu bulundu")
            
            return logs
            
        except Exception as e:
            logger.error(f"❌ Erişim logları getirme hatası: {str(e)}")
            logger.error(traceback.format_exc())
            return []
    
    def create_tables(self):
        """Gerekli tabloları oluştur (manuel olarak Supabase'de yapılmalı)"""
        tables_sql = """
        -- Plakalar tablosu
        CREATE TABLE IF NOT EXISTS plates (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            plate_number VARCHAR(20) UNIQUE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Erişim logları tablosu
        CREATE TABLE IF NOT EXISTS access_logs (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            plate_number VARCHAR(20) NOT NULL,
            vehicle_type VARCHAR(50),
            action VARCHAR(20) NOT NULL,
            success BOOLEAN DEFAULT TRUE,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- İndeksler
        CREATE INDEX IF NOT EXISTS idx_plates_number ON plates(plate_number);
        CREATE INDEX IF NOT EXISTS idx_access_logs_timestamp ON access_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_access_logs_plate ON access_logs(plate_number);
        """
        
        logger.info("📋 Tablo oluşturma SQL'i:")
        logger.info(tables_sql)
        return tables_sql 