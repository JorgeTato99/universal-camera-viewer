/**
 * 🎯 Paso de Éxito del Wizard
 * Muestra confirmación y próximos pasos
 */

import React from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
} from '@mui/material';
import { motion } from 'framer-motion';
import {
  CheckCircle as CheckIcon,
  PlayArrow as PlayIcon,
  Settings as SettingsIcon,
  VideoLibrary as VideoIcon,
  Dashboard as DashboardIcon,
} from '@mui/icons-material';
import { successAnimation, staggerContainer, staggerItem, buttonHover, buttonTap } from '../../animations/transitions';
import { ServerType } from '../useWizardState';

interface SuccessStepProps {
  serverType: ServerType;
  serverName: string;
  onFinish: () => void;
  onViewServers: () => void;
}

export const SuccessStep: React.FC<SuccessStepProps> = ({
  serverType,
  serverName,
  onFinish,
  onViewServers,
}) => {
  const nextSteps = [
    {
      icon: <PlayIcon />,
      title: 'Publicar una cámara',
      description: 'Ve a Cámaras y presiona el botón de publicar',
    },
    {
      icon: <VideoIcon />,
      title: 'Ver transmisiones activas',
      description: 'Monitorea el estado de tus streams en tiempo real',
    },
    {
      icon: <SettingsIcon />,
      title: 'Ajustar configuración',
      description: 'Personaliza la calidad y rendimiento del servidor',
    },
    {
      icon: <DashboardIcon />,
      title: 'Ver métricas',
      description: 'Analiza el uso de ancho de banda y espectadores',
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <Box sx={{ py: 3, textAlign: 'center' }}>
        {/* Ícono de éxito animado */}
        <motion.div
          variants={successAnimation}
          initial="initial"
          animate="animate"
          style={{ display: 'inline-block', marginBottom: 24 }}
        >
          <CheckIcon sx={{ fontSize: 80, color: 'success.main' }} />
        </motion.div>

        <Typography variant="h4" gutterBottom>
          ¡Servidor Configurado Exitosamente!
        </Typography>
        
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Tu servidor <strong>{serverName}</strong> está listo para transmitir cámaras
        </Typography>

        {/* Información del servidor */}
        <Paper 
          sx={{ 
            p: 3, 
            mb: 4, 
            maxWidth: 400, 
            mx: 'auto',
            background: (theme) => 
              theme.palette.mode === 'dark'
                ? 'linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(76, 175, 80, 0.05) 100%)'
                : 'linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%)',
          }}
        >
          <Typography variant="subtitle1" gutterBottom>
            Tipo de servidor: {serverType === 'remote' ? 'Remoto' : 'Local'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {serverType === 'remote' 
              ? 'Puedes acceder a tus cámaras desde cualquier lugar con internet'
              : 'Tus cámaras están disponibles dentro de tu red local'}
          </Typography>
        </Paper>

        {/* Próximos pasos */}
        <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
          Próximos pasos
        </Typography>

        <motion.div variants={staggerContainer} initial="initial" animate="animate">
          <List sx={{ maxWidth: 600, mx: 'auto' }}>
            {nextSteps.map((step, index) => (
              <motion.div key={index} variants={staggerItem}>
                <ListItem>
                  <ListItemIcon sx={{ color: 'primary.main' }}>
                    {step.icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={step.title}
                    secondary={step.description}
                  />
                </ListItem>
              </motion.div>
            ))}
          </List>
        </motion.div>

        {/* Tip adicional */}
        <Alert severity="info" sx={{ maxWidth: 600, mx: 'auto', mb: 4 }}>
          <Typography variant="body2">
            <strong>Consejo:</strong> Para mejores resultados, configura tus cámaras con una 
            resolución de 720p o 1080p y un bitrate entre 1-3 Mbps.
          </Typography>
        </Alert>

        {/* Botones de acción */}
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
          <motion.div whileHover={buttonHover} whileTap={buttonTap}>
            <Button
              variant="outlined"
              size="large"
              onClick={onViewServers}
            >
              Ver Mis Servidores
            </Button>
          </motion.div>

          <motion.div whileHover={buttonHover} whileTap={buttonTap}>
            <Button
              variant="contained"
              size="large"
              onClick={onFinish}
              sx={{
                background: (theme) => 
                  `linear-gradient(45deg, ${theme.palette.success.main} 30%, ${theme.palette.success.light} 90%)`,
                '&:hover': {
                  background: (theme) => 
                    `linear-gradient(45deg, ${theme.palette.success.dark} 30%, ${theme.palette.success.main} 90%)`,
                },
              }}
            >
              Ir a Publicar Cámaras
            </Button>
          </motion.div>
        </Box>
      </Box>
    </motion.div>
  );
};