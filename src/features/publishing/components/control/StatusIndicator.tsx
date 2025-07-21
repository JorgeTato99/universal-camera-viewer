/**
 * 🟢 Status Indicator Component - Universal Camera Viewer
 * Badge animado con tooltip informativo
 */

import React, { memo } from 'react';
import {
  Box,
  Chip,
  Tooltip,
  Typography,
  CircularProgress
} from '@mui/material';
import { keyframes } from '@mui/system';
import {
  FiberManualRecord as DotIcon,
  PlayArrow as RunningIcon,
  Stop as StoppedIcon,
  Error as ErrorIcon,
  HourglassEmpty as StartingIcon
} from '@mui/icons-material';

interface StatusIndicatorProps {
  status: 'idle' | 'starting' | 'running' | 'stopping' | 'error';
  label?: string;
  showIcon?: boolean;
  size?: 'small' | 'medium';
  errorMessage?: string;
  lastUpdate?: string;
}

// Animación de pulso para estado activo
const pulse = keyframes`
  0% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.1);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
`;

/**
 * Indicador de estado con animaciones
 */
export const StatusIndicator = memo<StatusIndicatorProps>(({
  status,
  label,
  showIcon = true,
  size = 'medium',
  errorMessage,
  lastUpdate
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'idle':
        return {
          color: '#9e9e9e',
          label: label || 'Inactivo',
          icon: <StoppedIcon />,
          chipColor: 'default' as const,
          animated: false
        };
      case 'starting':
        return {
          color: '#ff9800',
          label: label || 'Iniciando',
          icon: <StartingIcon />,
          chipColor: 'warning' as const,
          animated: true
        };
      case 'running':
        return {
          color: '#4caf50',
          label: label || 'Activo',
          icon: <RunningIcon />,
          chipColor: 'success' as const,
          animated: true
        };
      case 'stopping':
        return {
          color: '#ff9800',
          label: label || 'Deteniendo',
          icon: <CircularProgress size={16} />,
          chipColor: 'warning' as const,
          animated: true
        };
      case 'error':
        return {
          color: '#f44336',
          label: label || 'Error',
          icon: <ErrorIcon />,
          chipColor: 'error' as const,
          animated: false
        };
    }
  };

  const config = getStatusConfig();

  const tooltipContent = (
    <Box>
      <Typography variant="body2">
        Estado: {config.label}
      </Typography>
      {lastUpdate && (
        <Typography variant="caption" sx={{ display: 'block', mt: 0.5 }}>
          Última actualización: {new Date(lastUpdate).toLocaleTimeString('es-ES')}
        </Typography>
      )}
      {errorMessage && status === 'error' && (
        <Typography variant="caption" sx={{ display: 'block', mt: 0.5, color: 'error.light' }}>
          Error: {errorMessage}
        </Typography>
      )}
    </Box>
  );

  return (
    <Tooltip title={tooltipContent} arrow>
      <Chip
        label={config.label}
        color={config.chipColor}
        size={size}
        icon={showIcon ? (
          config.animated && status === 'running' ? (
            <Box
              component="span"
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                animation: `${pulse} 2s ease-in-out infinite`
              }}
            >
              <DotIcon sx={{ fontSize: size === 'small' ? 14 : 18 }} />
            </Box>
          ) : (
            config.icon
          )
        ) : undefined}
        sx={{
          fontWeight: 500,
          ...(config.animated && status === 'starting' && {
            animation: `${pulse} 1s ease-in-out infinite`
          })
        }}
      />
    </Tooltip>
  );
});

StatusIndicator.displayName = 'StatusIndicator';