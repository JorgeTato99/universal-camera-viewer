/**
 * 🎯 Paso de Bienvenida del Wizard
 * Explica la diferencia entre servidor local y remoto
 */

import React from 'react';
import { Box, Typography, Paper, Button, Grid } from '@mui/material';
import { motion } from 'framer-motion';
import {
  CloudQueue as CloudIcon,
  Computer as ComputerIcon,
  ArrowForward as ArrowIcon,
} from '@mui/icons-material';
import { fadeInOut, cardHover, buttonHover, buttonTap } from '../../animations/transitions';

interface WelcomeStepProps {
  onNext: () => void;
  onSkip: () => void;
}

export const WelcomeStep: React.FC<WelcomeStepProps> = ({ onNext, onSkip }) => {
  return (
    <motion.div
      variants={fadeInOut}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <Box sx={{ textAlign: 'center', py: 3 }}>
        <Typography variant="h4" gutterBottom>
          ¡Bienvenido a MediaMTX Publishing!
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}>
          Vamos a configurar tu primer servidor para transmitir cámaras. 
          Te guiaremos paso a paso en menos de 3 minutos.
        </Typography>

        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid size={{ xs: 12, md: 6 }}>
            <motion.div whileHover={cardHover}>
              <Paper
                sx={{
                  p: 3,
                  height: '100%',
                  cursor: 'pointer',
                  border: '2px solid transparent',
                  transition: 'border-color 0.3s',
                  '&:hover': {
                    borderColor: 'primary.main',
                  },
                }}
              >
                <CloudIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Servidor Remoto
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Accede a tus cámaras desde cualquier lugar del mundo. 
                  Ideal para monitoreo externo y compartir con otros.
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" color="success.main">
                    ✓ Acceso desde internet
                  </Typography>
                  <br />
                  <Typography variant="caption" color="success.main">
                    ✓ Sin configurar router
                  </Typography>
                  <br />
                  <Typography variant="caption" color="success.main">
                    ✓ Múltiples usuarios
                  </Typography>
                </Box>
              </Paper>
            </motion.div>
          </Grid>

          <Grid size={{ xs: 12, md: 6 }}>
            <motion.div whileHover={cardHover}>
              <Paper
                sx={{
                  p: 3,
                  height: '100%',
                  cursor: 'pointer',
                  border: '2px solid transparent',
                  transition: 'border-color 0.3s',
                  '&:hover': {
                    borderColor: 'success.main',
                  },
                }}
              >
                <ComputerIcon sx={{ fontSize: 48, color: 'success.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Servidor Local
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Ve tus cámaras solo dentro de tu red local. 
                  Máxima velocidad y privacidad para uso interno.
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" color="success.main">
                    ✓ Máxima velocidad
                  </Typography>
                  <br />
                  <Typography variant="caption" color="success.main">
                    ✓ 100% privado
                  </Typography>
                  <br />
                  <Typography variant="caption" color="success.main">
                    ✓ Sin internet
                  </Typography>
                </Box>
              </Paper>
            </motion.div>
          </Grid>
        </Grid>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Button
            variant="text"
            onClick={onSkip}
            sx={{ color: 'text.secondary' }}
          >
            Saltar configuración
          </Button>
          
          <motion.div
            whileHover={buttonHover}
            whileTap={buttonTap}
          >
            <Button
              variant="contained"
              size="large"
              endIcon={<ArrowIcon />}
              onClick={onNext}
              sx={{
                background: (theme) => 
                  `linear-gradient(45deg, ${theme.palette.primary.main} 30%, ${theme.palette.primary.light} 90%)`,
                boxShadow: '0 3px 5px 2px rgba(33, 150, 243, .3)',
                '&:hover': {
                  background: (theme) => 
                    `linear-gradient(45deg, ${theme.palette.primary.dark} 30%, ${theme.palette.primary.main} 90%)`,
                },
              }}
            >
              Comenzar Configuración
            </Button>
          </motion.div>
        </Box>
      </Box>
    </motion.div>
  );
};