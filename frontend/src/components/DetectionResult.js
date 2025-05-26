import React from 'react';
import {
  Box,
  Typography,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert
} from '@mui/material';
import {
  DirectionsCar,
  CreditCard,
  Security,
  CheckCircle,
  Cancel,
  Info
} from '@mui/icons-material';

const DetectionResult = ({ result }) => {
  if (!result) {
    return (
      <Alert severity="info">
        Henüz tespit sonucu yok
      </Alert>
    );
  }

  // Güven skorunu renklendir
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'error';
  };

  // Kapı durumunu renklendir
  const getGateActionColor = (action) => {
    switch (action) {
      case 'open': return 'success';
      case 'denied': return 'error';
      default: return 'default';
    }
  };

  // Kapı durumu ikonu
  const getGateActionIcon = (action) => {
    switch (action) {
      case 'open': return <CheckCircle color="success" />;
      case 'denied': return <Cancel color="error" />;
      default: return <Info color="info" />;
    }
  };

  // Kapı durumu metni
  const getGateActionText = (action) => {
    switch (action) {
      case 'open': return 'Kapı Açıldı';
      case 'denied': return 'Erişim Reddedildi';
      case 'closed': return 'Kapı Kapalı';
      default: return 'Bilinmiyor';
    }
  };

  return (
    <Box>
      {/* Ana Mesaj */}
      {result.message && (
        <Alert 
          severity={result.gate_action === 'open' ? 'success' : 
                   result.gate_action === 'denied' ? 'error' : 'info'}
          sx={{ mb: 2 }}
        >
          {result.message}
        </Alert>
      )}

      {/* Tespit Detayları */}
      <List dense>
        {/* Araç Tespiti */}
        <ListItem>
          <ListItemIcon>
            <DirectionsCar color={result.vehicle_detected ? 'success' : 'disabled'} />
          </ListItemIcon>
          <ListItemText
            primary="Araç Tespiti"
            secondary={
              <Box display="flex" alignItems="center" gap={1}>
                <Chip
                  label={result.vehicle_detected ? 'Tespit Edildi' : 'Tespit Edilmedi'}
                  color={result.vehicle_detected ? 'success' : 'default'}
                  size="small"
                />
                {result.vehicle_type && (
                  <Chip
                    label={result.vehicle_type}
                    variant="outlined"
                    size="small"
                  />
                )}
              </Box>
            }
          />
        </ListItem>

        {/* Güven Skoru */}
        {result.confidence > 0 && (
          <ListItem>
            <ListItemIcon>
              <Security color={getConfidenceColor(result.confidence)} />
            </ListItemIcon>
            <ListItemText
              primary="Güven Skoru"
              secondary={
                <Chip
                  label={`${(result.confidence * 100).toFixed(1)}%`}
                  color={getConfidenceColor(result.confidence)}
                  size="small"
                />
              }
            />
          </ListItem>
        )}

        <Divider sx={{ my: 1 }} />

        {/* Plaka Tespiti */}
        <ListItem>
          <ListItemIcon>
            <CreditCard color={result.plate_detected ? 'success' : 'disabled'} />
          </ListItemIcon>
          <ListItemText
            primary="Plaka Tespiti"
            secondary={
              <Box display="flex" alignItems="center" gap={1}>
                <Chip
                  label={result.plate_detected ? 'Okundu' : 'Okunamadı'}
                  color={result.plate_detected ? 'success' : 'default'}
                  size="small"
                />
                {result.plate_text && (
                  <Chip
                    label={result.plate_text}
                    variant="outlined"
                    size="small"
                    sx={{ 
                      fontFamily: 'monospace',
                      fontWeight: 'bold'
                    }}
                  />
                )}
              </Box>
            }
          />
        </ListItem>

        <Divider sx={{ my: 1 }} />

        {/* Kapı Durumu */}
        <ListItem>
          <ListItemIcon>
            {getGateActionIcon(result.gate_action)}
          </ListItemIcon>
          <ListItemText
            primary="Kapı Durumu"
            secondary={
              <Chip
                label={getGateActionText(result.gate_action)}
                color={getGateActionColor(result.gate_action)}
                size="small"
              />
            }
          />
        </ListItem>
      </List>

      {/* Ek Bilgiler */}
      <Box mt={2}>
        <Typography variant="caption" color="text.secondary">
          Tespit Zamanı: {new Date().toLocaleString('tr-TR')}
        </Typography>
      </Box>

      {/* Debug Bilgileri (geliştirme için) */}
      {process.env.NODE_ENV === 'development' && (
        <Box mt={2} p={2} bgcolor="grey.100" borderRadius={1}>
          <Typography variant="caption" component="div">
            <strong>Debug:</strong>
          </Typography>
          <Typography variant="caption" component="pre" sx={{ fontSize: '0.7rem' }}>
            {JSON.stringify(result, null, 2)}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default DetectionResult; 