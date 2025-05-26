-- Araç Kapısı & Plaka Tespit Sistemi
-- Supabase Veritabanı Kurulum SQL'i

-- 1. Plakalar tablosu
CREATE TABLE IF NOT EXISTS plates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    plate_number VARCHAR(20) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Erişim logları tablosu
CREATE TABLE IF NOT EXISTS access_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    plate_number VARCHAR(20) NOT NULL,
    vehicle_type VARCHAR(50),x
    action VARCHAR(20) NOT NULL, -- 'open', 'denied'
    success BOOLEAN DEFAULT TRUE,
    confidence FLOAT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Sistem logları tablosu (opsiyonel)
CREATE TABLE IF NOT EXISTS system_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    level VARCHAR(20) NOT NULL, -- 'INFO', 'WARNING', 'ERROR'
    message TEXT NOT NULL,
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- İndeksler
CREATE INDEX IF NOT EXISTS idx_plates_number ON plates(plate_number);
CREATE INDEX IF NOT EXISTS idx_plates_created_at ON plates(created_at);

CREATE INDEX IF NOT EXISTS idx_access_logs_timestamp ON access_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_access_logs_plate ON access_logs(plate_number);
CREATE INDEX IF NOT EXISTS idx_access_logs_action ON access_logs(action);

CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);

-- RLS (Row Level Security) politikaları
ALTER TABLE plates ENABLE ROW LEVEL SECURITY;
ALTER TABLE access_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_logs ENABLE ROW LEVEL SECURITY;

-- Basit politikalar (tüm işlemler için izin ver)
-- Gerçek projede daha kısıtlayıcı politikalar kullanın
CREATE POLICY "Enable all operations for plates" ON plates
    FOR ALL USING (true);

CREATE POLICY "Enable all operations for access_logs" ON access_logs
    FOR ALL USING (true);

CREATE POLICY "Enable all operations for system_logs" ON system_logs
    FOR ALL USING (true);

-- Örnek veri ekleme
INSERT INTO plates (plate_number) VALUES 
    ('34ABC1234'),
    ('06DEF5678'),
    ('35GHI9012')
ON CONFLICT (plate_number) DO NOTHING;

-- Trigger fonksiyonu: updated_at otomatik güncelleme
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger: plates tablosu için updated_at güncelleme
CREATE TRIGGER update_plates_updated_at 
    BEFORE UPDATE ON plates 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Görünümler (Views)
-- Son 100 erişim logu
CREATE OR REPLACE VIEW recent_access_logs AS
SELECT 
    al.*,
    p.created_at as plate_registered_at
FROM access_logs al
LEFT JOIN plates p ON al.plate_number = p.plate_number
ORDER BY al.timestamp DESC
LIMIT 100;

-- Günlük istatistikler
CREATE OR REPLACE VIEW daily_stats AS
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as total_attempts,
    COUNT(CASE WHEN action = 'open' THEN 1 END) as successful_entries,
    COUNT(CASE WHEN action = 'denied' THEN 1 END) as denied_entries,
    COUNT(DISTINCT plate_number) as unique_plates
FROM access_logs
WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Fonksiyonlar
-- Plaka istatistikleri
CREATE OR REPLACE FUNCTION get_plate_stats(plate_num VARCHAR)
RETURNS TABLE(
    plate_number VARCHAR,
    total_attempts BIGINT,
    successful_entries BIGINT,
    last_access TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        plate_num,
        COUNT(*),
        COUNT(CASE WHEN action = 'open' THEN 1 END),
        MAX(timestamp)
    FROM access_logs
    WHERE access_logs.plate_number = plate_num;
END;
$$ LANGUAGE plpgsql;

-- Kurulum tamamlandı mesajı
DO $$
BEGIN
    RAISE NOTICE 'Araç Kapısı & Plaka Tespit Sistemi veritabanı kurulumu tamamlandı!';
    RAISE NOTICE 'Oluşturulan tablolar: plates, access_logs, system_logs';
    RAISE NOTICE 'Oluşturulan görünümler: recent_access_logs, daily_stats';
    RAISE NOTICE 'Oluşturulan fonksiyonlar: get_plate_stats()';
END $$; 