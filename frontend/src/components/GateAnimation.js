import React from 'react';
import { Box, Typography } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, Cancel, Lock } from '@mui/icons-material';

const GateAnimation = ({ isOpen, isDenied }) => {
  // Kapı durumunu belirle
  const getGateStatus = () => {
    if (isOpen) return 'open';
    if (isDenied) return 'denied';
    return 'closed';
  };

  const gateStatus = getGateStatus();

  // Animasyon varyantları
  const gateVariants = {
    closed: {
      scaleX: 1,
      backgroundColor: '#666',
      transition: { duration: 0.5 }
    },
    open: {
      scaleX: 0.1,
      backgroundColor: '#4caf50',
      transition: { duration: 1, ease: "easeInOut" }
    },
    denied: {
      scaleX: 1,
      backgroundColor: '#f44336',
      transition: { duration: 0.3 }
    }
  };

  const iconVariants = {
    hidden: { scale: 0, opacity: 0 },
    visible: { 
      scale: 1, 
      opacity: 1,
      transition: { duration: 0.5, delay: 0.2 }
    }
  };

  const textVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { 
      y: 0, 
      opacity: 1,
      transition: { duration: 0.5, delay: 0.4 }
    }
  };

  // Durum rengini al
  const getStatusColor = () => {
    switch (gateStatus) {
      case 'open': return '#4caf50';
      case 'denied': return '#f44336';
      default: return '#666';
    }
  };

  // Durum ikonunu al
  const getStatusIcon = () => {
    switch (gateStatus) {
      case 'open': return <CheckCircle sx={{ fontSize: 60, color: '#4caf50' }} />;
      case 'denied': return <Cancel sx={{ fontSize: 60, color: '#f44336' }} />;
      default: return <Lock sx={{ fontSize: 60, color: '#666' }} />;
    }
  };

  // Durum metnini al
  const getStatusText = () => {
    switch (gateStatus) {
      case 'open': return 'Kapı Açık';
      case 'denied': return 'Erişim Reddedildi';
      default: return 'Kapı Kapalı';
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 200,
        position: 'relative'
      }}
    >
      {/* Kapı Çerçevesi */}
      <Box
        sx={{
          width: 200,
          height: 120,
          border: '4px solid #333',
          borderRadius: 2,
          position: 'relative',
          overflow: 'hidden',
          mb: 3
        }}
      >
        {/* Kapı */}
        <motion.div
          variants={gateVariants}
          animate={gateStatus}
          style={{
            width: '100%',
            height: '100%',
            transformOrigin: 'left center',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          {/* Kapı Kolu */}
          <Box
            sx={{
              width: 8,
              height: 8,
              bgcolor: '#333',
              borderRadius: '50%',
              position: 'absolute',
              right: 20,
              top: '50%',
              transform: 'translateY(-50%)'
            }}
          />
        </motion.div>

        {/* Açık Kapı Efekti */}
        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'linear-gradient(90deg, transparent 0%, rgba(76, 175, 80, 0.3) 100%)',
                pointerEvents: 'none'
              }}
            />
          )}
        </AnimatePresence>

        {/* Reddedildi Efekti */}
        <AnimatePresence>
          {isDenied && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ 
                opacity: [0, 1, 0],
                transition: { duration: 0.5, repeat: 2 }
              }}
              exit={{ opacity: 0 }}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: 'rgba(244, 67, 54, 0.3)',
                pointerEvents: 'none'
              }}
            />
          )}
        </AnimatePresence>
      </Box>

      {/* Durum İkonu */}
      <motion.div
        variants={iconVariants}
        initial="hidden"
        animate="visible"
        key={gateStatus}
      >
        {getStatusIcon()}
      </motion.div>

      {/* Durum Metni */}
      <motion.div
        variants={textVariants}
        initial="hidden"
        animate="visible"
        key={gateStatus}
      >
        <Typography
          variant="h6"
          align="center"
          sx={{
            color: getStatusColor(),
            fontWeight: 'bold',
            mt: 1
          }}
        >
          {getStatusText()}
        </Typography>
      </motion.div>

      {/* Işık Efekti */}
      <Box
        sx={{
          position: 'absolute',
          top: -10,
          left: '50%',
          transform: 'translateX(-50%)',
          width: 20,
          height: 20,
          borderRadius: '50%',
          bgcolor: getStatusColor(),
          boxShadow: `0 0 20px ${getStatusColor()}`,
          opacity: gateStatus === 'closed' ? 0.3 : 1,
          transition: 'all 0.5s ease'
        }}
      />

      {/* Hareket Çizgileri (Açık durumda) */}
      <AnimatePresence>
        {isOpen && (
          <>
            {[...Array(3)].map((_, i) => (
              <motion.div
                key={i}
                initial={{ x: -50, opacity: 0 }}
                animate={{ 
                  x: 50, 
                  opacity: [0, 1, 0],
                  transition: { 
                    duration: 1, 
                    delay: i * 0.2,
                    repeat: Infinity,
                    repeatDelay: 1
                  }
                }}
                style={{
                  position: 'absolute',
                  top: `${40 + i * 15}%`,
                  left: '20%',
                  width: 30,
                  height: 2,
                  backgroundColor: '#4caf50',
                  borderRadius: 1
                }}
              />
            ))}
          </>
        )}
      </AnimatePresence>
    </Box>
  );
};

export default GateAnimation; 