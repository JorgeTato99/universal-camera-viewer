/**
 * 🎯 Paso de Configuración del Servidor
 * Formulario simplificado con validación en tiempo real
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  FormControlLabel,
  Checkbox,
  Alert,
  InputAdornment,
  Collapse,
  Paper,
  IconButton,
  Tooltip,
} from '@mui/material';
import { motion } from 'framer-motion';
import {
  ArrowBack as BackIcon,
  ArrowForward as NextIcon,
  Api as ApiIcon,
  Lock as LockIcon,
  LockOpen as LockOpenIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  HelpOutline as HelpIcon,
} from '@mui/icons-material';
import { slideFromRight, buttonHover, buttonTap } from '../../animations/transitions';
import { ServerType, WizardState } from '../useWizardState';

interface ConfigurationStepProps {
  serverType: ServerType;
  config: WizardState['serverConfig'];
  onUpdateConfig: (config: Partial<WizardState['serverConfig']>) => void;
  onNext: () => void;
  onBack: () => void;
}

export const ConfigurationStep: React.FC<ConfigurationStepProps> = ({
  serverType,
  config,
  onUpdateConfig,
  onNext,
  onBack,
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Validación en tiempo real
  useEffect(() => {
    const newErrors: Record<string, string> = {};

    if (!config.name.trim()) {
      newErrors.name = 'El nombre es obligatorio';
    }

    if (!config.api_url.match(/^https?:\/\/.+/)) {
      newErrors.api_url = 'Debe ser una URL válida (http:// o https://)';
    }

    if (config.auth_required && !config.username?.trim()) {
      newErrors.username = 'El usuario es obligatorio si requiere autenticación';
    }

    if (config.auth_required && !config.password?.trim()) {
      newErrors.password = 'La contraseña es obligatoria si requiere autenticación';
    }

    setErrors(newErrors);
  }, [config]);

  const isValid = Object.keys(errors).length === 0 && config.name.trim();

  const handleNext = () => {
    if (isValid) {
      onNext();
    }
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
          Configurar Servidor {serverType === 'remote' ? 'Remoto' : 'Local'}
        </Typography>
        <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 4 }}>
          Completa la información de conexión del servidor
        </Typography>

        <Paper sx={{ p: 3, maxWidth: 600, mx: 'auto' }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Nombre del servidor */}
            <TextField
              label="Nombre del servidor"
              value={config.name}
              onChange={(e) => onUpdateConfig({ name: e.target.value })}
              error={!!errors.name && config.name.length > 0}
              helperText={config.name.length > 0 ? errors.name : 'Ej: Mi servidor principal'}
              fullWidth
              required
              slotProps={{
                input: {
                  endAdornment: (
                    <Tooltip title="Un nombre descriptivo para identificar este servidor">
                      <IconButton size="small">
                        <HelpIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  ),
                },
              }}
            />

            {/* URL de API */}
            <TextField
              label="URL de API"
              value={config.api_url}
              onChange={(e) => onUpdateConfig({ api_url: e.target.value })}
              error={!!errors.api_url}
              helperText={
                errors.api_url || 
                (serverType === 'remote' 
                  ? 'URL del servidor remoto. Ej: http://servidor.com:9997'
                  : 'URL local del servidor. Ej: http://localhost:9997')
              }
              fullWidth
              required
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <ApiIcon sx={{ color: 'action.active' }} />
                    </InputAdornment>
                  ),
                },
              }}
            />

            {/* Autenticación */}
            <Box>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={config.auth_required}
                    onChange={(e) => onUpdateConfig({ auth_required: e.target.checked })}
                    icon={<LockOpenIcon />}
                    checkedIcon={<LockIcon />}
                    sx={{
                      color: 'action.active',
                      '&.Mui-checked': {
                        color: 'warning.main',
                      },
                    }}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">
                      El servidor requiere autenticación
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Activa esto si tu servidor necesita usuario y contraseña
                    </Typography>
                  </Box>
                }
              />

              <Collapse in={config.auth_required}>
                <Box sx={{ mt: 2, pl: 4, display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <TextField
                    label="Usuario"
                    value={config.username || ''}
                    onChange={(e) => onUpdateConfig({ username: e.target.value })}
                    error={!!errors.username}
                    helperText={errors.username}
                    fullWidth
                    autoComplete="username"
                    size="small"
                  />

                  <TextField
                    label="Contraseña"
                    type={showPassword ? 'text' : 'password'}
                    value={config.password || ''}
                    onChange={(e) => onUpdateConfig({ password: e.target.value })}
                    error={!!errors.password}
                    helperText={errors.password}
                    fullWidth
                    autoComplete="new-password"
                    size="small"
                    slotProps={{
                      input: {
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton
                              onClick={() => setShowPassword(!showPassword)}
                              edge="end"
                              size="small"
                            >
                              {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                            </IconButton>
                          </InputAdornment>
                        ),
                      },
                    }}
                  />
                </Box>
              </Collapse>
            </Box>

            {/* Nota informativa */}
            {serverType === 'remote' && (
              <Alert severity="info">
                Asegúrate de tener los datos de conexión proporcionados por tu proveedor de servidor MediaMTX.
              </Alert>
            )}

            {serverType === 'local' && (
              <Alert severity="info">
                El servidor local debe estar ejecutándose en esta misma computadora para funcionar correctamente.
              </Alert>
            )}
          </Box>
        </Paper>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
          <Button
            variant="outlined"
            startIcon={<BackIcon />}
            onClick={onBack}
          >
            Atrás
          </Button>

          <motion.div
            whileHover={isValid ? buttonHover : {}}
            whileTap={isValid ? buttonTap : {}}
          >
            <Button
              variant="contained"
              endIcon={<NextIcon />}
              onClick={handleNext}
              disabled={!isValid}
            >
              Probar Conexión
            </Button>
          </motion.div>
        </Box>
      </Box>
    </motion.div>
  );
};