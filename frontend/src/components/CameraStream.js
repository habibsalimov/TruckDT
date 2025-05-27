import React, { useRef, useCallback, useState, useEffect } from 'react';
import { 
  Box, 
  Button, 
  Alert, 
  CircularProgress, 
  Typography, 
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent
} from '@mui/material';
import { 
  Stop, 
  PlayArrow, 
  Refresh,
  CameraAlt
} from '@mui/icons-material';
import { toast } from 'react-toastify';
import axios from 'axios';

const CameraStream = ({ onDetectionResult, onProcessingChange }) => {
  const [isActive, setIsActive] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [cameras, setCameras] = useState([]);
  const [selectedCamera, setSelectedCamera] = useState(1);
  const [detectionActive, setDetectionActive] = useState(false);
  const [streamUrl, setStreamUrl] = useState('');
  const [cameraInfo, setCameraInfo] = useState(null);

  // Backend API base URL
  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5001';

  // Kamera listesini yükle
  const loadCameras = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/camera/list`);
      setCameras(response.data.cameras || []);
      setCameraInfo(response.data);
      
      if (response.data.current_camera) {
        setSelectedCamera(response.data.current_camera);
      }
      
      setIsActive(response.data.camera_active || false);
      setDetectionActive(response.data.camera_active || false); // Kamera aktifse tespit de aktif
    } catch (error) {
      console.error('Kamera listesi yüklenemedi:', error);
      toast.error('Kamera listesi yüklenemedi');
    }
  }, [API_BASE]);

  // Sayfa yüklendiğinde kamera listesini al
  useEffect(() => {
    loadCameras();
  }, [loadCameras]);

  // Stream URL'ini güncelle
  useEffect(() => {
    if (isActive) {
      setStreamUrl(`${API_BASE}/api/camera/stream?t=${Date.now()}`);
    } else {
      setStreamUrl('');
    }
  }, [isActive, API_BASE]);

  // Gerçek zamanlı tespiti otomatik başlat
  const startDetection = async () => {
    try {
      const response = await axios.post(`${API_BASE}/api/detection/start`);
      if (response.data.success) {
        setDetectionActive(true);
        toast.success('🎯 Gerçek zamanlı tespit başlatıldı');
      }
    } catch (error) {
      console.error('Tespit başlatma hatası:', error);
      toast.error('Tespit başlatılamadı');
    }
  };

  // Kamera başlat
  const startCamera = async () => {
    try {
      setIsProcessing(true);
      setError(null);

      const response = await axios.post(`${API_BASE}/api/camera/start`, {
        camera_id: selectedCamera
      });

      if (response.data.success) {
        setIsActive(true);
        toast.success(`📹 Kamera ${selectedCamera} başlatıldı`);
        
        // Kamera başlatıldıktan sonra otomatik olarak tespiti başlat
        setTimeout(() => {
          startDetection();
        }, 1000); // 1 saniye bekle
        
        await loadCameras(); // Durumu güncelle
      } else {
        throw new Error(response.data.message);
      }
    } catch (error) {
      console.error('Kamera başlatma hatası:', error);
      setError(error.response?.data?.message || 'Kamera başlatılamadı');
      toast.error('Kamera başlatılamadı');
    } finally {
      setIsProcessing(false);
    }
  };

  // Kamera durdur
  const stopCamera = async () => {
    try {
      setIsProcessing(true);

      // Önce tespiti durdur
      try {
        await axios.post(`${API_BASE}/api/detection/stop`);
      } catch (error) {
        console.warn('Tespit durdurma uyarısı:', error);
      }

      const response = await axios.post(`${API_BASE}/api/camera/stop`);

      if (response.data.success) {
        setIsActive(false);
        setDetectionActive(false);
        toast.success('📹 Kamera durduruldu');
        await loadCameras(); // Durumu güncelle
      } else {
        throw new Error(response.data.message);
      }
    } catch (error) {
      console.error('Kamera durdurma hatası:', error);
      toast.error('Kamera durdurulamadı');
    } finally {
      setIsProcessing(false);
    }
  };

  // Tespit sonuçlarını kontrol etmek için polling
  useEffect(() => {
    let pollingInterval;
    
    if (detectionActive) {
      pollingInterval = setInterval(async () => {
        try {
          const response = await axios.get(`${API_BASE}/api/detection/latest`);
          if (response.data.has_result) {
            // Tespit sonucunu parent bileşene gönder
            onDetectionResult(response.data.result);
          }
        } catch (error) {
          // Polling hatalarını sessizce logla
          console.debug('Polling hatası (normal):', error.message);
        }
      }, 1000); // Her saniye kontrol et
    }
    
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [detectionActive, API_BASE, onDetectionResult]);

  return (
    <Box>
      {/* Hata Mesajı */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Kamera Görüntüsü */}
      <Box 
        sx={{ 
          position: 'relative',
          border: '2px solid #ddd',
          borderRadius: 2,
          overflow: 'hidden',
          bgcolor: '#000',
          minHeight: 360,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          mb: 2
        }}
      >
        {isActive && streamUrl ? (
          <>
            <img
              src={streamUrl}
              alt="Kamera Stream"
              style={{
                width: '100%',
                height: 'auto',
                display: 'block',
                maxHeight: '500px',
                objectFit: 'contain'
              }}
              onError={(e) => {
                console.error('Stream yükleme hatası');
                setError('Kamera stream\'i yüklenemedi');
              }}
            />

            {/* Durum Göstergeleri */}
            <Box
              sx={{
                position: 'absolute',
                top: 10,
                left: 10,
                display: 'flex',
                flexDirection: 'column',
                gap: 1
              }}
            >
              {/* Canlı Göstergesi */}
              <Box
                sx={{
                  bgcolor: 'rgba(0,0,0,0.7)',
                  color: 'white',
                  px: 2,
                  py: 1,
                  borderRadius: 1
                }}
              >
                <Typography variant="body2">
                  🔴 CANLI - Kamera {selectedCamera}
                </Typography>
              </Box>

              {/* Tespit Durumu */}
              {detectionActive && (
                <Box
                  sx={{
                    bgcolor: 'rgba(0,255,0,0.8)',
                    color: 'black',
                    px: 2,
                    py: 1,
                    borderRadius: 1
                  }}
                >
                  <Typography variant="body2">
                    🎯 GERÇEK ZAMANLI TESPİT AKTİF
                  </Typography>
                </Box>
              )}
            </Box>
          </>
        ) : (
          <Box sx={{ textAlign: 'center', color: 'white' }}>
            <CameraAlt sx={{ fontSize: 80, mb: 2, opacity: 0.5 }} />
            <Typography variant="h6">
              {isProcessing ? 'Kamera başlatılıyor...' : 'Kamera kapalı'}
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              {cameras.length > 0 
                ? 'Kamerayı başlatmak için aşağıdaki kontrolleri kullanın'
                : 'Kamera bulunamadı. Yenile butonunu deneyin.'
              }
            </Typography>
          </Box>
        )}
      </Box>

      {/* Kamera Kontrolleri */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            🎥 Kamera Kontrolleri
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            {/* Kamera Seçimi */}
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Kamera</InputLabel>
              <Select
                value={selectedCamera}
                label="Kamera"
                onChange={(e) => setSelectedCamera(e.target.value)}
                disabled={isActive || isProcessing}
              >
                {cameras.map((camera) => (
                  <MenuItem key={camera.id} value={camera.id}>
                    Kamera {camera.id} ({camera.resolution})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Kamera Başlat/Durdur */}
            <Button
              variant={isActive ? "outlined" : "contained"}
              color={isActive ? "error" : "primary"}
              startIcon={isActive ? <Stop /> : <PlayArrow />}
              onClick={isActive ? stopCamera : startCamera}
              disabled={isProcessing}
              size="large"
            >
              {isActive ? 'Kamerayı Durdur' : 'Kamerayı Başlat'}
            </Button>

            {/* Kamera Listesini Yenile */}
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={loadCameras}
              disabled={isProcessing}
            >
              Yenile
            </Button>
          </Box>

          {/* Kamera Durumu */}
          {cameraInfo && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Durum: {isActive ? '🟢 Aktif' : '🔴 Pasif'} | 
                Tespit: {detectionActive ? '🎯 Gerçek Zamanlı Açık' : '⏸️ Kapalı'} |
                Seçili Kamera: {selectedCamera}
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Bilgi Mesajı */}
      <Box sx={{ mt: 2 }}>
        <Alert severity="info">
          <Typography variant="body2">
            🚛 <strong>Otomatik Tespit:</strong> Kamera başlatıldığında gerçek zamanlı araç tespiti otomatik olarak aktif hale gelir. 
            Sistem sürekli olarak kamyon/tır araçlarını tespit eder ve plaka okuma işlemini gerçekleştirir.
          </Typography>
        </Alert>
      </Box>
    </Box>
  );
};

export default CameraStream; 