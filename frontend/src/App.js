import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, AppBar, Toolbar, Typography, Container } from '@mui/material';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Sayfalar
import Home from './pages/Home';
import Plates from './pages/Plates';

// Tema oluştur
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <div className="App">
          {/* Üst Menü */}
          <AppBar position="static" elevation={2}>
            <Toolbar>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                🚛 Araç Kapısı Kontrol Sistemi
              </Typography>
            </Toolbar>
          </AppBar>

          {/* Ana İçerik */}
          <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/plates" element={<Plates />} />
            </Routes>
          </Container>

          {/* Toast Bildirimleri */}
          <ToastContainer
            position="top-right"
            autoClose={5000}
            hideProgressBar={false}
            newestOnTop={false}
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
            theme="light"
          />
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App; 