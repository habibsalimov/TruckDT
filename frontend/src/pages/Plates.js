import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Chip,
  CircularProgress,
  InputAdornment
} from '@mui/material';
import {
  Add,
  Delete,
  Search,
  DirectionsCar,
  Home
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import axios from 'axios';

function Plates() {
  const navigate = useNavigate();
  const [plates, setPlates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [newPlate, setNewPlate] = useState('');
  const [addingPlate, setAddingPlate] = useState(false);

  // Sayfa yüklendiğinde plakaları getir
  useEffect(() => {
    fetchPlates();
  }, []);

  // Plakaları getir
  const fetchPlates = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/plates');
      setPlates(response.data.plates || []);
    } catch (error) {
      console.error('Plaka getirme hatası:', error);
      toast.error('Plakalar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  // Yeni plaka ekle
  const handleAddPlate = async () => {
    if (!newPlate.trim()) {
      toast.error('Plaka numarası boş olamaz');
      return;
    }

    // Basit plaka formatı kontrolü
    const plateRegex = /^[0-9]{2}[A-Z]{1,3}[0-9]{1,4}$/;
    const cleanPlate = newPlate.toUpperCase().replace(/\s/g, '');
    
    if (!plateRegex.test(cleanPlate)) {
      toast.error('Geçersiz plaka formatı (örn: 34ABC1234)');
      return;
    }

    try {
      setAddingPlate(true);
      const response = await axios.post('/api/plates', {
        plate_number: cleanPlate
      });

      if (response.data.success) {
        toast.success(response.data.message);
        setNewPlate('');
        setOpenDialog(false);
        fetchPlates(); // Listeyi yenile
      } else {
        toast.error(response.data.error || 'Plaka eklenemedi');
      }
    } catch (error) {
      console.error('Plaka ekleme hatası:', error);
      if (error.response?.data?.error) {
        toast.error(error.response.data.error);
      } else {
        toast.error('Plaka ekleme başarısız');
      }
    } finally {
      setAddingPlate(false);
    }
  };

  // Plaka sil
  const handleDeletePlate = async (plateId, plateNumber) => {
    if (!window.confirm(`${plateNumber} plakasını silmek istediğinizden emin misiniz?`)) {
      return;
    }

    try {
      const response = await axios.delete(`/api/plates/${plateId}`);
      
      if (response.data.success) {
        toast.success(response.data.message);
        fetchPlates(); // Listeyi yenile
      } else {
        toast.error(response.data.error || 'Plaka silinemedi');
      }
    } catch (error) {
      console.error('Plaka silme hatası:', error);
      toast.error('Plaka silme başarısız');
    }
  };

  // Plaka arama
  const filteredPlates = plates.filter(plate =>
    plate.plate_number.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Tarih formatla
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('tr-TR');
  };

  return (
    <Box>
      {/* Başlık ve Navigasyon */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          <DirectionsCar sx={{ mr: 1, verticalAlign: 'middle' }} />
          Plaka Yönetimi
        </Typography>
        
        <Button
          variant="outlined"
          startIcon={<Home />}
          onClick={() => navigate('/')}
        >
          Ana Sayfa
        </Button>
      </Box>

      {/* Kontrol Paneli */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Box display="flex" gap={2} alignItems="center" flexWrap="wrap">
          {/* Arama */}
          <TextField
            placeholder="Plaka ara..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
            sx={{ minWidth: 250 }}
          />

          {/* Yeni Plaka Ekle */}
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setOpenDialog(true)}
          >
            Yeni Plaka Ekle
          </Button>

          {/* İstatistikler */}
          <Box ml="auto" display="flex" gap={2}>
            <Chip
              label={`Toplam: ${plates.length}`}
              color="primary"
              variant="outlined"
            />
            {searchTerm && (
              <Chip
                label={`Bulunan: ${filteredPlates.length}`}
                color="secondary"
                variant="outlined"
              />
            )}
          </Box>
        </Box>
      </Paper>

      {/* Plaka Listesi */}
      <Paper elevation={3}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Plaka Numarası</strong></TableCell>
                <TableCell><strong>Eklenme Tarihi</strong></TableCell>
                <TableCell align="center"><strong>İşlemler</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={3} align="center" sx={{ py: 4 }}>
                    <CircularProgress />
                    <Typography variant="body2" sx={{ mt: 2 }}>
                      Plakalar yükleniyor...
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : filteredPlates.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} align="center" sx={{ py: 4 }}>
                    <Typography variant="body1" color="text.secondary">
                      {searchTerm ? 'Arama kriterine uygun plaka bulunamadı' : 'Henüz plaka eklenmemiş'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredPlates.map((plate) => (
                  <TableRow key={plate.id} hover>
                    <TableCell>
                      <Typography
                        variant="h6"
                        sx={{
                          fontFamily: 'monospace',
                          fontWeight: 'bold',
                          color: 'primary.main'
                        }}
                      >
                        {plate.plate_number}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatDate(plate.created_at)}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        color="error"
                        onClick={() => handleDeletePlate(plate.id, plate.plate_number)}
                        title="Plakayı Sil"
                      >
                        <Delete />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Yeni Plaka Ekleme Dialogu */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Yeni Plaka Ekle</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            Türk plaka formatında giriniz (örn: 34ABC1234)
          </Alert>
          
          <TextField
            autoFocus
            margin="dense"
            label="Plaka Numarası"
            fullWidth
            variant="outlined"
            value={newPlate}
            onChange={(e) => setNewPlate(e.target.value.toUpperCase())}
            placeholder="34ABC1234"
            inputProps={{
              style: { fontFamily: 'monospace', fontSize: '1.2rem' }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>
            İptal
          </Button>
          <Button
            onClick={handleAddPlate}
            variant="contained"
            disabled={addingPlate}
            startIcon={addingPlate ? <CircularProgress size={20} /> : <Add />}
          >
            {addingPlate ? 'Ekleniyor...' : 'Ekle'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Bilgi Notu */}
      <Alert severity="info" sx={{ mt: 3 }}>
        <Typography variant="body2">
          <strong>Not:</strong> Bu listede bulunan plakalar sisteme giriş yapabilir. 
          Kamyon veya tır tespit edildiğinde, plaka bu listede kontrol edilir ve 
          eşleşme durumunda kapı otomatik olarak açılır.
        </Typography>
      </Alert>
    </Box>
  );
}

export default Plates; 