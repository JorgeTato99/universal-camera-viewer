/**
 * 🎯 Management Status Bar Component
 * Barra de estado con resumen de información del dashboard
 */

import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  LinearProgress,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Videocam as CameraIcon,
  WifiTethering as ConnectedIcon,
  PlayCircle as ActiveIcon,
  Warning as AlertIcon,
} from '@mui/icons-material';

interface ManagementStatusBarProps {
  totalCameras: number;
  connectedCameras: number;
  activeCameras: number;
  alerts: number;
}

interface StatusItemProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  color?: string;
  showProgress?: boolean;
  total?: number;
}

const StatusItem: React.FC<StatusItemProps> = ({
  icon,
  label,
  value,
  color,
  showProgress,
  total,
}) => {
  const theme = useTheme();
  const percentage = total ? (value / total) * 100 : 0;

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        px: 3,
        borderRight: 1,
        borderColor: 'divider',
        '&:last-child': {
          borderRight: 0,
        },
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 40,
          height: 40,
          borderRadius: '50%',
          bgcolor: color ? alpha(color, 0.1) : alpha(theme.palette.primary.main, 0.1),
          color: color || 'primary.main',
        }}
      >
        {icon}
      </Box>
      
      <Box sx={{ flex: 1 }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
          {label}
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
          <Typography variant="h6" fontWeight={600}>
            {value}
          </Typography>
          
          {showProgress && total && (
            <Typography variant="body2" color="text.secondary">
              / {total}
            </Typography>
          )}
        </Box>
        
        {showProgress && total && (
          <LinearProgress
            variant="determinate"
            value={percentage}
            sx={{
              mt: 0.5,
              height: 4,
              borderRadius: 2,
              bgcolor: alpha(theme.palette.primary.main, 0.1),
              '& .MuiLinearProgress-bar': {
                borderRadius: 2,
                bgcolor: color || 'primary.main',
              },
            }}
          />
        )}
      </Box>
    </Box>
  );
};

export const ManagementStatusBar: React.FC<ManagementStatusBarProps> = ({
  totalCameras,
  connectedCameras,
  activeCameras,
  alerts,
}) => {
  const theme = useTheme();

  return (
    <Paper
      elevation={0}
      sx={{
        borderTop: 1,
        borderColor: 'divider',
        bgcolor: 'background.paper',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          height: 80,
          px: 2,
        }}
      >
        {/* Total de cámaras */}
        <StatusItem
          icon={<CameraIcon />}
          label="Total Cámaras"
          value={totalCameras}
        />

        {/* Cámaras conectadas */}
        <StatusItem
          icon={<ConnectedIcon />}
          label="Conectadas"
          value={connectedCameras}
          color={theme.palette.success.main}
          showProgress
          total={totalCameras}
        />

        {/* Cámaras activas (streaming) */}
        <StatusItem
          icon={<ActiveIcon />}
          label="Transmitiendo"
          value={activeCameras}
          color={theme.palette.info.main}
          showProgress
          total={connectedCameras}
        />

        {/* Alertas */}
        <StatusItem
          icon={<AlertIcon />}
          label="Alertas"
          value={alerts}
          color={alerts > 0 ? theme.palette.warning.main : theme.palette.text.secondary}
        />

        {/* Espaciador */}
        <Box sx={{ flex: 1 }} />

        {/* Estado general del sistema */}
        <Box sx={{ px: 3 }}>
          <Chip
            label={alerts > 0 ? 'Sistema con alertas' : 'Sistema operativo'}
            color={alerts > 0 ? 'warning' : 'success'}
            size="small"
            sx={{ fontWeight: 600 }}
          />
        </Box>
      </Box>
    </Paper>
  );
};