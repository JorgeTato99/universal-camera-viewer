/**
 * 🎯 Paso de Selección de Tipo de Servidor
 * El usuario elige entre servidor remoto o local
 */

import React from 'react';
import { Box, Typography, Paper, Button, Chip } from '@mui/material';
import { motion } from 'framer-motion';
import {
  CloudQueue as CloudIcon,
  Computer as ComputerIcon,
  ArrowBack as BackIcon,
  Recommend as RecommendIcon,
} from '@mui/icons-material';
import { slideFromRight, cardHover, buttonHover, buttonTap } from '../../animations/transitions';
import { ServerType } from '../useWizardState';

interface ServerTypeStepProps {
  selectedType: ServerType | null;
  onSelectType: (type: ServerType) => void;
  onNext: () => void;
  onBack: () => void;
}

export const ServerTypeStep: React.FC<ServerTypeStepProps> = ({
  selectedType,
  onSelectType,
  onNext,
  onBack,
}) => {
  const handleSelect = (type: ServerType) => {
    onSelectType(type);
    // Auto-avanzar después de seleccionar
    setTimeout(() => onNext(), 300);
  };

  return (
    <motion.div
      variants={slideFromRight}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <Box sx={{ py: 3 }}>
        <Typography variant="h5" gutterBottom align="center">
          ¿Qué tipo de servidor deseas configurar?
        </Typography>
        <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 4 }}>
          Elige según dónde necesitas ver tus cámaras
        </Typography>

        <Box sx={{ display: 'flex', gap: 3, justifyContent: 'center', mb: 4 }}>
          <motion.div whileHover={cardHover}>
            <Paper
              onClick={() => handleSelect('remote')}
              sx={{
                p: 4,
                width: 280,
                cursor: 'pointer',
                position: 'relative',
                border: '3px solid',
                borderColor: selectedType === 'remote' ? 'primary.main' : 'transparent',
                transition: 'all 0.3s',
                '&:hover': {
                  borderColor: selectedType === 'remote' ? 'primary.main' : 'primary.light',
                },
              }}
            >
              {/* Chip de recomendado */}
              <Chip
                icon={<RecommendIcon />}
                label="Recomendado"
                color="primary"
                size="small"
                sx={{
                  position: 'absolute',
                  top: 16,
                  right: 16,
                }}
              />

              <Box sx={{ textAlign: 'center' }}>
                <CloudIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Servidor Remoto
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Para ver tus cámaras desde cualquier lugar con internet
                </Typography>

                <Box sx={{ mt: 2, textAlign: 'left' }}>
                  <Typography variant="caption" display="block" sx={{ mb: 0.5 }}>
                    ✅ Acceso desde móvil/PC
                  </Typography>
                  <Typography variant="caption" display="block" sx={{ mb: 0.5 }}>
                    ✅ Compartir con familia
                  </Typography>
                  <Typography variant="caption" display="block">
                    ✅ Notificaciones remotas
                  </Typography>
                </Box>

                <motion.div
                  whileHover={buttonHover}
                  whileTap={buttonTap}
                  style={{ marginTop: 16 }}
                >
                  <Button
                    variant={selectedType === 'remote' ? 'contained' : 'outlined'}
                    fullWidth
                    color="primary"
                  >
                    {selectedType === 'remote' ? 'Seleccionado' : 'Seleccionar'}
                  </Button>
                </motion.div>
              </Box>
            </Paper>
          </motion.div>

          <motion.div whileHover={cardHover}>
            <Paper
              onClick={() => handleSelect('local')}
              sx={{
                p: 4,
                width: 280,
                cursor: 'pointer',
                border: '3px solid',
                borderColor: selectedType === 'local' ? 'success.main' : 'transparent',
                transition: 'all 0.3s',
                '&:hover': {
                  borderColor: selectedType === 'local' ? 'success.main' : 'success.light',
                },
              }}
            >
              <Box sx={{ textAlign: 'center' }}>
                <ComputerIcon sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Servidor Local
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Solo para ver dentro de tu red local (casa/oficina)
                </Typography>

                <Box sx={{ mt: 2, textAlign: 'left' }}>
                  <Typography variant="caption" display="block" sx={{ mb: 0.5 }}>
                    ✅ Máxima velocidad
                  </Typography>
                  <Typography variant="caption" display="block" sx={{ mb: 0.5 }}>
                    ✅ Total privacidad
                  </Typography>
                  <Typography variant="caption" display="block">
                    ✅ Sin costos externos
                  </Typography>
                </Box>

                <motion.div
                  whileHover={buttonHover}
                  whileTap={buttonTap}
                  style={{ marginTop: 16 }}
                >
                  <Button
                    variant={selectedType === 'local' ? 'contained' : 'outlined'}
                    fullWidth
                    color="success"
                  >
                    {selectedType === 'local' ? 'Seleccionado' : 'Seleccionar'}
                  </Button>
                </motion.div>
              </Box>
            </Paper>
          </motion.div>
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Button
            variant="outlined"
            startIcon={<BackIcon />}
            onClick={onBack}
          >
            Atrás
          </Button>
        </Box>
      </Box>
    </motion.div>
  );
};