/**
 * Diálogo de autenticación para servidores MediaMTX remotos
 * 
 * Permite a los usuarios autenticarse con un servidor remoto proporcionando
 * credenciales. Muestra feedback visual del estado de autenticación.
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton,
  Chip,
} from '@mui/material';
import {
  Key as KeyIcon,
  Visibility,
  VisibilityOff,
  Person as PersonIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { mediamtxAuthService } from '../../../services/publishing/mediamtxAuthService';

interface ServerAuthDialogProps {
  open: boolean;
  onClose: () => void;
  server: {
    id: number;
    name: string;
    apiUrl: string;
    isAuthenticated?: boolean;
    lastAuthError?: string;
  };
  onAuthSuccess?: () => void;
}

export const ServerAuthDialog: React.FC<ServerAuthDialogProps> = ({
  open,
  onClose,
  server,
  onAuthSuccess,
}) => {
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleInputChange = (field: 'username' | 'password') => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setCredentials({ ...credentials, [field]: event.target.value });
    setError(null);
  };

  const handleSubmit = async () => {
    if (!credentials.username || !credentials.password) {
      setError('Por favor, complete todos los campos');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await mediamtxAuthService.login(
        server.id,
        credentials.username,
        credentials.password
      );

      if (result.success) {
        setSuccess(true);
        
        // Esperar un momento para mostrar éxito antes de cerrar
        setTimeout(() => {
          onAuthSuccess?.();
          handleClose();
        }, 1500);
      } else {
        setError(result.error || 'Error de autenticación');
      }
    } catch (err: any) {
      setError(err.message || 'Error al conectar con el servidor');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setCredentials({ username: '', password: '' });
      setError(null);
      setSuccess(false);
      onClose();
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !loading) {
      handleSubmit();
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          overflow: 'hidden',
        },
      }}
    >
      <DialogTitle
        sx={{
          bgcolor: 'primary.main',
          color: 'primary.contrastText',
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <KeyIcon />
        Autenticación - {server.name}
      </DialogTitle>

      <DialogContent sx={{ mt: 3 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Estado actual */}
          {server.isAuthenticated && !success && (
            <Alert
              severity="info"
              icon={<CheckCircleIcon />}
              sx={{ mb: 1 }}
            >
              Ya está autenticado con este servidor. Puede actualizar las credenciales si lo desea.
            </Alert>
          )}

          {/* Mensaje de error previo */}
          {server.lastAuthError && !error && !success && (
            <Alert severity="warning" sx={{ mb: 1 }}>
              {server.lastAuthError}
            </Alert>
          )}

          {/* Información del servidor */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Servidor API
            </Typography>
            <Chip
              label={server.apiUrl}
              size="small"
              variant="outlined"
              sx={{ fontFamily: 'monospace' }}
            />
          </Box>

          {/* Campos de credenciales */}
          <TextField
            label="Usuario"
            value={credentials.username}
            onChange={handleInputChange('username')}
            onKeyPress={handleKeyPress}
            disabled={loading || success}
            fullWidth
            required
            autoFocus
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <PersonIcon color="action" />
                </InputAdornment>
              ),
            }}
            placeholder="jorge.cliente"
          />

          <TextField
            label="Contraseña"
            type={showPassword ? 'text' : 'password'}
            value={credentials.password}
            onChange={handleInputChange('password')}
            onKeyPress={handleKeyPress}
            disabled={loading || success}
            fullWidth
            required
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <KeyIcon color="action" />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                    disabled={loading || success}
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
            placeholder="••••••••"
          />

          {/* Mensajes de estado */}
          {error && (
            <Alert severity="error" icon={<ErrorIcon />}>
              {error}
            </Alert>
          )}

          {success && (
            <Alert severity="success" icon={<CheckCircleIcon />}>
              ¡Autenticación exitosa! Conectando...
            </Alert>
          )}

          {/* Nota informativa */}
          {!error && !success && (
            <Typography variant="caption" color="text.secondary">
              Las credenciales se almacenan de forma segura y encriptada.
              La sesión se mantendrá activa hasta que expire el token.
            </Typography>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 2, gap: 1 }}>
        <Button
          onClick={handleClose}
          disabled={loading}
          color="inherit"
        >
          Cancelar
        </Button>
        <Button
          onClick={handleSubmit}
          disabled={loading || success || !credentials.username || !credentials.password}
          variant="contained"
          startIcon={loading ? <CircularProgress size={20} /> : <KeyIcon />}
        >
          {loading ? 'Autenticando...' : 'Autenticar'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};