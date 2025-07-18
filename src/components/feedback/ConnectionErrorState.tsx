/**
 * 🚨 Connection Error State Component - Universal Camera Viewer
 * Componente para mostrar errores de conexión con el backend
 * Sigue los principios de Material Design 3 y la arquitectura MVP
 */

import { memo } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Stack,
  useTheme,
  alpha,
  CircularProgress,
} from '@mui/material';
import {
  CloudOff as OfflineIcon,
  Refresh as RetryIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

interface ConnectionErrorStateProps {
  /** Tipo de error para personalizar el mensaje */
  errorType?: 'connection' | 'server' | 'timeout' | 'unknown';
  /** Mensaje de error personalizado (opcional) */
  customMessage?: string;
  /** Callback para reintentar la conexión */
  onRetry?: () => void;
  /** Indica si está intentando reconectar */
  isRetrying?: boolean;
  /** Muestra información adicional de debug (solo en desarrollo) */
  showDebugInfo?: boolean;
  /** Detalles técnicos del error */
  errorDetails?: string;
}

/**
 * Componente optimizado con memo para mostrar estados de error de conexión
 * Proporciona feedback visual claro al usuario cuando el backend no está disponible
 */
export const ConnectionErrorState = memo<ConnectionErrorStateProps>(({
  errorType = 'connection',
  customMessage,
  onRetry,
  isRetrying = false,
  showDebugInfo = process.env.NODE_ENV === 'development',
  errorDetails,
}) => {
  const theme = useTheme();

  /**
   * Obtiene el icono apropiado según el tipo de error
   */
  const getErrorIcon = () => {
    switch (errorType) {
      case 'connection':
        return <OfflineIcon sx={{ fontSize: 80, color: theme.palette.error.main }} />;
      case 'server':
        return <WarningIcon sx={{ fontSize: 80, color: theme.palette.warning.main }} />;
      case 'timeout':
        return <InfoIcon sx={{ fontSize: 80, color: theme.palette.info.main }} />;
      default:
        return <WarningIcon sx={{ fontSize: 80, color: theme.palette.error.main }} />;
    }
  };

  /**
   * Obtiene el mensaje principal según el tipo de error
   */
  const getErrorTitle = () => {
    if (customMessage) return customMessage;
    
    switch (errorType) {
      case 'connection':
        return 'No se puede conectar con el servidor';
      case 'server':
        return 'Error en el servidor';
      case 'timeout':
        return 'La conexión tardó demasiado tiempo';
      default:
        return 'Ha ocurrido un error inesperado';
    }
  };

  /**
   * Obtiene el mensaje descriptivo según el tipo de error
   */
  const getErrorDescription = () => {
    switch (errorType) {
      case 'connection':
        return 'Verifica que el servidor backend esté ejecutándose en el puerto 8000';
      case 'server':
        return 'El servidor encontró un error. Por favor, intenta nuevamente más tarde';
      case 'timeout':
        return 'La solicitud tardó demasiado tiempo. Verifica tu conexión a internet';
      default:
        return 'Por favor, intenta nuevamente o contacta al soporte técnico';
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '400px',
        p: 4,
        width: '100%',
      }}
    >
      <Paper
        elevation={0}
        sx={{
          p: 4,
          maxWidth: 600,
          width: '100%',
          textAlign: 'center',
          bgcolor: alpha(theme.palette.background.paper, 0.8),
          border: `1px solid ${theme.palette.divider}`,
          borderRadius: 2,
        }}
      >
        <Stack spacing={3} alignItems="center">
          {/* Icono del error con animación sutil */}
          <Box
            sx={{
              animation: 'pulse 2s ease-in-out infinite',
              '@keyframes pulse': {
                '0%': { opacity: 0.8 },
                '50%': { opacity: 1 },
                '100%': { opacity: 0.8 },
              },
            }}
          >
            {getErrorIcon()}
          </Box>

          {/* Título del error */}
          <Typography variant="h5" color="text.primary" fontWeight={600}>
            {getErrorTitle()}
          </Typography>

          {/* Descripción del error */}
          <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 400 }}>
            {getErrorDescription()}
          </Typography>

          {/* Información técnica (solo en desarrollo) */}
          {showDebugInfo && errorDetails && (
            <Paper
              variant="outlined"
              sx={{
                p: 2,
                width: '100%',
                bgcolor: alpha(theme.palette.error.main, 0.05),
                borderColor: theme.palette.error.main,
              }}
            >
              <Typography variant="caption" color="error.main" fontFamily="monospace">
                {errorDetails}
              </Typography>
            </Paper>
          )}

          {/* Sugerencias de solución */}
          <Paper
            variant="outlined"
            sx={{
              p: 2,
              width: '100%',
              bgcolor: alpha(theme.palette.info.main, 0.05),
              borderColor: theme.palette.info.main,
            }}
          >
            <Typography variant="subtitle2" color="info.main" gutterBottom>
              Pasos sugeridos:
            </Typography>
            <Stack spacing={1} alignItems="flex-start" sx={{ pl: 2 }}>
              <Typography variant="body2" color="text.secondary">
                1. Verifica que el servidor backend esté ejecutándose
              </Typography>
              <Typography variant="body2" color="text.secondary">
                2. Ejecuta: <code style={{ backgroundColor: alpha(theme.palette.text.primary, 0.1), padding: '2px 4px', borderRadius: '4px' }}>python run_python.py</code>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                3. Verifica que no haya errores en la consola del servidor
              </Typography>
            </Stack>
          </Paper>

          {/* Botón de reintentar */}
          {onRetry && (
            <Button
              variant="contained"
              size="large"
              onClick={onRetry}
              disabled={isRetrying}
              startIcon={isRetrying ? <CircularProgress size={20} /> : <RetryIcon />}
              sx={{
                mt: 2,
                minWidth: 200,
                transition: 'all 0.2s',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: theme.shadows[4],
                },
              }}
            >
              {isRetrying ? 'Reintentando...' : 'Reintentar conexión'}
            </Button>
          )}
        </Stack>
      </Paper>
    </Box>
  );
});

// Añadir displayName para debugging
ConnectionErrorState.displayName = 'ConnectionErrorState';