import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  DirectionsCar,
  LocalShipping,
  Security,
  CameraAlt,
  CheckCircle,
  Cancel
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

// Bileşenler
import CameraStream from '../components/CameraStream';
import DetectionResult from '../components/DetectionResult';
import GateAnimation from '../components/GateAnimation';

function Home() {
  const navigate = useNavigate();
  const [detectionResult, setDetectionResult] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [systemStatus, setSystemStatus] = useState('ready'); // ready, processing, success, denied
  const [lastDetection, setLastDetection] = useState(null);

  // Sistem durumu kontrolü
  useEffect(() => {
    checkSystemHealth();
  }, []);

  const checkSystemHealth = async () => {
    try {
      const response = await fetch('/api/health');
      if (response.ok) {
        console.log('Sistem sağlıklı');
      }
    } catch (error) {
      console.error('Sistem sağlık kontrolü başarısız:', error);
    }
  };

  const handleDetectionResult = (result) => {
    setDetectionResult(result);
    setLastDetection(new Date().toLocaleTimeString('tr-TR'));
    
    // Sistem durumunu güncelle
    if (result.gate_action === 'open') {
      setSystemStatus('success');
    } else if (result.gate_action === 'denied') {
      setSystemStatus('denied');
    } else {
      setSystemStatus('ready');
    }

    // 5 saniye sonra durumu sıfırla
    setTimeout(() => {
      setSystemStatus('ready');
    }, 5000);
  };

  const handleProcessingChange = (processing) => {
    setIsProcessing(processing);
    if (processing) {
      setSystemStatus('processing');
    }
  };

  const getStatusColor = () => {
    switch (systemStatus) {
      case 'success': return 'success';
      case 'denied': return 'error';
      case 'processing': return 'warning';
      default: return 'primary';
    }
  };

  const getStatusIcon = () => {
    switch (systemStatus) {
      case 'success': return <CheckCircle />;
      case 'denied': return <Cancel />;
      case 'processing': return <CircularProgress size={24} />;
      default: return <Security />;
    }
  };

  const getStatusText = () => {
    switch (systemStatus) {
      case 'success': return 'Kapı Açıldı';
      case 'denied': return 'Erişim Reddedildi';
      case 'processing': return 'İşleniyor...';
      default: return 'Sistem Hazır';
    }
  };

  return (
    <Box>
      {/* Sistem Durumu */}
      <Paper elevation={3} sx={{ p: 3, mb: 3, bgcolor: getStatusColor() + '.light' }}>
        <Box display="flex" alignItems="center" justifyContent="center">
          {getStatusIcon()}
          <Typography variant="h4" sx={{ ml: 2, color: getStatusColor() + '.dark' }}>
            {getStatusText()}
          </Typography>
        </Box>
        {lastDetection && (
          <Typography variant="body2" align="center" sx={{ mt: 1, opacity: 0.8 }}>
            Son tespit: {lastDetection}
          </Typography>
        )}
      </Paper>

      <Grid container spacing={3}>
        {/* Sol Panel - Kamera ve Kontroller */}
        <Grid item xs={12} md={8}>
          <Paper elevation={3} sx={{ p: 3, height: 'fit-content' }}>
            <Typography variant="h5" gutterBottom>
              <CameraAlt sx={{ mr: 1, verticalAlign: 'middle' }} />
              Canlı Kamera Görüntüsü
            </Typography>
            
            <CameraStream 
              onDetectionResult={handleDetectionResult}
              onProcessingChange={handleProcessingChange}
            />

            <Box mt={2} display="flex" gap={2} justifyContent="center">
              <Button
                variant="outlined"
                onClick={() => navigate('/plates')}
                startIcon={<DirectionsCar />}
              >
                Plaka Yönetimi
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Sağ Panel - Sonuçlar ve Animasyon */}
        <Grid item xs={12} md={4}>
          {/* Kapı Animasyonu */}
          <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom align="center">
              Kapı Durumu
            </Typography>
            <GateAnimation 
              isOpen={systemStatus === 'success'}
              isDenied={systemStatus === 'denied'}
            />
          </Paper>

          {/* Tespit Sonuçları */}
          {detectionResult && (
            <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Tespit Sonuçları
              </Typography>
              <DetectionResult result={detectionResult} />
            </Paper>
          )}

          {/* Sistem Bilgileri */}
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Sistem Bilgileri
            </Typography>
            
            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <LocalShipping color="primary" sx={{ mr: 1 }} />
                  <Typography variant="subtitle2">
                    Araç Tespiti
                  </Typography>
                </Box>
                <Chip 
                  label="Aktif" 
                  color="success" 
                  size="small"
                />
              </CardContent>
            </Card>

            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <Security color="primary" sx={{ mr: 1 }} />
                  <Typography variant="subtitle2">
                    Plaka Okuma
                  </Typography>
                </Box>
                <Chip 
                  label="Aktif" 
                  color="success" 
                  size="small"
                />
              </CardContent>
            </Card>

            <Alert severity="info" sx={{ mt: 2 }}>
              Sistem sadece kamyon ve tır araçları için plaka kontrolü yapar.
            </Alert>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Home; 