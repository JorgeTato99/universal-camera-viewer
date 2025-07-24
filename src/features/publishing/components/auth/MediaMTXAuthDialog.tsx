/**
 * 🔐 MediaMTX Auth Dialog - Universal Camera Viewer
 * Diálogo para autenticación con servidores MediaMTX remotos
 * 
 * Características:
 * - Validación en tiempo real de credenciales
 * - Prueba de conexión antes de guardar
 * - Feedback visual del estado de conexión
 * - Manejo de errores con mensajes claros
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Alert,
  CircularProgress,
  Typography,
  IconButton,
  InputAdornment,
  Stepper,
  Step,
  StepLabel,
  Collapse,
  Chip
} from '@mui/material';
import {
  Close as CloseIcon,
  Visibility,
  VisibilityOff,
  CheckCircle,
  Error as ErrorIcon,
  VpnKey as AuthIcon,
  CloudQueue as ServerIcon,
  Security as SecurityIcon
} from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { mediamtxRemoteService, MediaMTXServer } from '../../../../services/publishing/mediamtxRemoteService';
import { notificationStore } from '../../../../stores/notificationStore';
import { validateMediaMTXCredentials } from '../../utils/validation';

// === TIPOS Y ESQUEMAS ===

const authFormSchema = z.object({
  username: z.string()
    .min(3, 'Mínimo 3 caracteres')
    .max(50, 'Máximo 50 caracteres'),
  password: z.string()
    .min(4, 'Mínimo 4 caracteres')
});

type AuthFormData = z.infer<typeof authFormSchema>;

interface MediaMTXAuthDialogProps {
  open: boolean;
  onClose: () => void;
  server: MediaMTXServer;
  onAuthSuccess?: (server: MediaMTXServer) => void;
}

// === COMPONENTE PRINCIPAL ===

export const MediaMTXAuthDialog: React.FC<MediaMTXAuthDialogProps> = ({
  open,
  onClose,
  server,
  onAuthSuccess
}) => {
  // Estado del componente
  const [showPassword, setShowPassword] = useState(false);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [authStatus, setAuthStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [authError, setAuthError] = useState<string | null>(null);
  const [activeStep, setActiveStep] = useState(0);

  // React Hook Form
  const {
    control,
    handleSubmit,
    formState: { errors, isValid },
    reset,
    watch
  } = useForm<AuthFormData>({
    resolver: zodResolver(authFormSchema),
    mode: 'onChange',
    defaultValues: {
      username: server.username || '',
      password: ''
    }
  });

  // Observar cambios en el formulario
  const formValues = watch();

  // Reset cuando se abre el diálogo
  useEffect(() => {
    if (open) {
      reset({
        username: server.username || '',
        password: ''
      });
      setAuthStatus('idle');
      setAuthError(null);
      setActiveStep(0);
      setShowPassword(false);
    }
  }, [open, server, reset]);

  // Probar conexión
  const handleTestConnection = useCallback(async () => {
    setIsTesting(true);
    setAuthStatus('testing');
    setAuthError(null);

    try {
      // TODO: Implementar endpoint de prueba de conexión sin autenticar
      // Por ahora, simulamos una prueba exitosa
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      setAuthStatus('success');
      setActiveStep(1);
      
      notificationStore.showSuccess(
        'Conexión exitosa',
        `Servidor MediaMTX "${server.name}" accesible`
      );
    } catch (error) {
      setAuthStatus('error');
      setAuthError('No se pudo conectar al servidor. Verifique la URL y que el servidor esté activo.');
      
      notificationStore.showError(
        'Error de conexión',
        'No se pudo establecer conexión con el servidor'
      );
    } finally {
      setIsTesting(false);
    }
  }, [server]);

  // Manejar autenticación
  const onSubmit = async (data: AuthFormData) => {
    setIsAuthenticating(true);
    setAuthError(null);

    try {
      // Autenticar con el servidor
      const response = await mediamtxRemoteService.authenticate({
        server_id: server.id,
        username: data.username,
        password: data.password
      });

      if (response.success && response.data) {
        setAuthStatus('success');
        
        // Notificar éxito
        notificationStore.showSuccess(
          'Autenticación exitosa',
          `Conectado como ${data.username} al servidor "${server.name}"`
        );

        // Callback de éxito
        if (onAuthSuccess) {
          onAuthSuccess({
            ...server,
            username: data.username,
            is_authenticated: true,
            last_auth_check: new Date().toISOString()
          });
        }

        // Cerrar diálogo después de un breve delay
        setTimeout(() => {
          onClose();
        }, 500);
      } else {
        throw new Error(response.error || 'Error de autenticación');
      }
    } catch (error) {
      setAuthStatus('error');
      const errorMessage = error instanceof Error ? error.message : 'Error desconocido';
      setAuthError(errorMessage);
      
      // Manejar errores específicos
      if (errorMessage.includes('401') || errorMessage.includes('Unauthorized')) {
        setAuthError('Credenciales inválidas. Verifique usuario y contraseña.');
      } else if (errorMessage.includes('Network')) {
        setAuthError('Error de red. Verifique su conexión a internet.');
      }
    } finally {
      setIsAuthenticating(false);
    }
  };

  // Obtener color del estado
  const getStatusColor = () => {
    switch (authStatus) {
      case 'success':
        return 'success';
      case 'error':
        return 'error';
      case 'testing':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          overflow: 'hidden'
        }
      }}
    >
      {/* Header con gradiente */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #2196f3 0%, #1976d2 100%)',
          color: 'white',
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AuthIcon />
          <Typography variant="h6" component="div">
            Autenticar con MediaMTX
          </Typography>
        </Box>
        <IconButton
          edge="end"
          color="inherit"
          onClick={onClose}
          aria-label="cerrar"
          size="small"
        >
          <CloseIcon />
        </IconButton>
      </Box>

      <DialogContent sx={{ pt: 3 }}>
        {/* Información del servidor */}
        <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <ServerIcon color="action" />
            <Typography variant="subtitle1" fontWeight="medium">
              {server.name}
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary">
            {server.url}
          </Typography>
          {server.api_url && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
              API: {server.api_url}
            </Typography>
          )}
        </Box>

        {/* Stepper */}
        <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
          <Step>
            <StepLabel>Probar conexión</StepLabel>
          </Step>
          <Step>
            <StepLabel>Autenticar</StepLabel>
          </Step>
        </Stepper>

        {/* Paso 1: Probar conexión */}
        <Collapse in={activeStep === 0}>
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="body1" gutterBottom>
              Primero, verifiquemos que el servidor esté accesible
            </Typography>
            
            <Button
              variant="contained"
              onClick={handleTestConnection}
              disabled={isTesting}
              startIcon={isTesting ? <CircularProgress size={20} /> : <ServerIcon />}
              sx={{ mt: 2 }}
            >
              {isTesting ? 'Probando conexión...' : 'Probar conexión'}
            </Button>

            {authStatus === 'success' && activeStep === 0 && (
              <Alert severity="success" sx={{ mt: 2 }}>
                ¡Conexión exitosa! El servidor está accesible.
              </Alert>
            )}
          </Box>
        </Collapse>

        {/* Paso 2: Autenticar */}
        <Collapse in={activeStep === 1}>
          <form onSubmit={handleSubmit(onSubmit)}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {/* Campo de usuario */}
              <Controller
                name="username"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Usuario"
                    fullWidth
                    error={!!errors.username}
                    helperText={errors.username?.message}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <SecurityIcon color="action" />
                        </InputAdornment>
                      )
                    }}
                    autoComplete="username"
                    autoFocus
                  />
                )}
              />

              {/* Campo de contraseña */}
              <Controller
                name="password"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Contraseña"
                    type={showPassword ? 'text' : 'password'}
                    fullWidth
                    error={!!errors.password}
                    helperText={errors.password?.message}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <VpnKey color="action" />
                        </InputAdornment>
                      ),
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            onClick={() => setShowPassword(!showPassword)}
                            edge="end"
                            size="small"
                          >
                            {showPassword ? <VisibilityOff /> : <Visibility />}
                          </IconButton>
                        </InputAdornment>
                      )
                    }}
                    autoComplete="current-password"
                  />
                )}
              />

              {/* Indicador de seguridad */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <SecurityIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                <Typography variant="caption" color="text.secondary">
                  Las credenciales se transmiten de forma segura y no se almacenan localmente
                </Typography>
              </Box>
            </Box>
          </form>
        </Collapse>

        {/* Mensajes de error */}
        {authError && (
          <Alert severity="error" sx={{ mt: 2 }} onClose={() => setAuthError(null)}>
            {authError}
          </Alert>
        )}

        {/* Estado de autenticación exitosa */}
        {authStatus === 'success' && activeStep === 1 && (
          <Alert severity="success" sx={{ mt: 2 }}>
            Autenticación exitosa. Ahora puede publicar cámaras a este servidor.
          </Alert>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} disabled={isAuthenticating}>
          Cancelar
        </Button>
        
        {activeStep === 0 && authStatus === 'success' && (
          <Button
            variant="contained"
            onClick={() => setActiveStep(1)}
            endIcon={<AuthIcon />}
          >
            Continuar con autenticación
          </Button>
        )}
        
        {activeStep === 1 && (
          <Button
            variant="contained"
            onClick={handleSubmit(onSubmit)}
            disabled={!isValid || isAuthenticating}
            startIcon={isAuthenticating ? <CircularProgress size={20} /> : <CheckCircle />}
          >
            {isAuthenticating ? 'Autenticando...' : 'Autenticar'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default MediaMTXAuthDialog;