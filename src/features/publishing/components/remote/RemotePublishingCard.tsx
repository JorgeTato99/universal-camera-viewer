/**
 * 🎥 Remote Publishing Card - Universal Camera Viewer
 * Card para control de publicación de cámaras a servidores MediaMTX remotos
 * 
 * Características:
 * - Control de publicación (iniciar/detener/reiniciar)
 * - Visualización de métricas en tiempo real
 * - Indicadores de estado con colores semánticos
 * - Selector de servidor remoto integrado
 */

import React, { memo, useState, useCallback, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Box,
  Typography,
  IconButton,
  Tooltip,
  Collapse,
  Divider,
  Chip,
  LinearProgress,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Skeleton
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Refresh,
  MoreVert,
  Videocam,
  CloudUpload,
  Error as ErrorIcon,
  Info as InfoIcon,
  Speed,
  People,
  Timer,
  ExpandMore,
  ExpandLess,
  Settings,
  Launch
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { StatusIndicator } from '../control/StatusIndicator';
import { PublishingControlButton } from '../control/PublishingControlButton';
import { RemoteMetricsDisplay } from './RemoteMetricsDisplay';
import { 
  RemotePublishStatus, 
  mediamtxRemoteService,
  MediaMTXServer 
} from '../../../../services/publishing/mediamtxRemoteService';
import { PublishingStatus } from '../../types';
import { getPublishingStatusLabel } from '../../../../utils/statusLabels';
import { formatDuration } from '../../../../utils/time';

// === STYLED COMPONENTS ===

const StyledCard = styled(Card)(({ theme }) => ({
  position: 'relative',
  transition: 'all 0.3s ease',
  '&:hover': {
    boxShadow: theme.shadows[4],
  }
}));

const StatusBar = styled(Box)<{ status: string }>(({ theme, status }) => {
  const getColor = () => {
    switch (status) {
      case PublishingStatus.PUBLISHING:
        return theme.palette.success.main;
      case PublishingStatus.ERROR:
        return theme.palette.error.main;
      case PublishingStatus.STARTING:
      case PublishingStatus.STOPPING:
        return theme.palette.warning.main;
      default:
        return theme.palette.grey[400];
    }
  };

  return {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 4,
    backgroundColor: getColor(),
    transition: 'background-color 0.3s ease'
  };
});

const MetricBox = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(0.5),
  padding: theme.spacing(0.5, 1),
  borderRadius: theme.shape.borderRadius,
  backgroundColor: theme.palette.grey[100],
  ...theme.applyStyles('dark', {
    backgroundColor: theme.palette.grey[800]
  })
}));

// === INTERFACES ===

interface RemotePublishingCardProps {
  cameraId: string;
  cameraName: string;
  remotePublication?: RemotePublishStatus;
  availableServers: MediaMTXServer[];
  selectedServerId?: number;
  onServerSelect: (serverId: number) => void;
  onStart: (cameraId: string, serverId: number) => Promise<void>;
  onStop: (cameraId: string) => Promise<void>;
  onRestart?: (cameraId: string) => Promise<void>;
  onOpenViewer?: () => void;
  onConfigure?: () => void;
  isLoading?: boolean;
}

// === COMPONENTE PRINCIPAL ===

export const RemotePublishingCard = memo<RemotePublishingCardProps>(({
  cameraId,
  cameraName,
  remotePublication,
  availableServers,
  selectedServerId,
  onServerSelect,
  onStart,
  onStop,
  onRestart,
  onOpenViewer,
  onConfigure,
  isLoading = false
}) => {
  // Estado local
  const [expanded, setExpanded] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Estado derivado
  const isPublishing = remotePublication?.status === PublishingStatus.PUBLISHING;
  const hasError = remotePublication?.status === PublishingStatus.ERROR;
  const currentServer = availableServers.find(s => s.id === (remotePublication?.server_id || selectedServerId));

  // Manejadores
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setMenuAnchor(event.currentTarget);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
  };

  const handleStart = useCallback(async () => {
    if (!currentServer) return;
    
    setIsProcessing(true);
    try {
      await onStart(cameraId, currentServer.id);
    } finally {
      setIsProcessing(false);
    }
  }, [cameraId, currentServer, onStart]);

  const handleStop = useCallback(async () => {
    setIsProcessing(true);
    try {
      await onStop(cameraId);
    } finally {
      setIsProcessing(false);
    }
  }, [cameraId, onStop]);

  const handleRestart = useCallback(async () => {
    if (!onRestart) return;
    
    setIsProcessing(true);
    try {
      await onRestart(cameraId);
    } finally {
      setIsProcessing(false);
    }
  }, [cameraId, onRestart]);

  // Renderizar contenido de la card
  const renderCardContent = () => {
    if (isLoading) {
      return (
        <Box>
          <Skeleton variant="text" width="60%" />
          <Skeleton variant="text" width="40%" />
          <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
            <Skeleton variant="rectangular" width={100} height={32} />
            <Skeleton variant="rectangular" width={100} height={32} />
          </Box>
        </Box>
      );
    }

    return (
      <>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box sx={{ flex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Videocam color="action" />
              <Typography variant="h6" component="h3">
                {cameraName}
              </Typography>
            </Box>
            
            {currentServer && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                <CloudUpload sx={{ fontSize: 16, color: 'text.secondary' }} />
                <Typography variant="body2" color="text.secondary">
                  {currentServer.name}
                </Typography>
              </Box>
            )}
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {remotePublication && (
              <StatusIndicator
                status={remotePublication.status.toLowerCase() as any}
                size="small"
              />
            )}
            
            <IconButton size="small" onClick={handleMenuOpen}>
              <MoreVert />
            </IconButton>
          </Box>
        </Box>

        {/* Métricas rápidas */}
        {isPublishing && remotePublication && (
          <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <MetricBox>
              <Speed sx={{ fontSize: 16 }} />
              <Typography variant="caption">
                {remotePublication.metrics.fps} FPS
              </Typography>
            </MetricBox>
            
            <MetricBox>
              <People sx={{ fontSize: 16 }} />
              <Typography variant="caption">
                {remotePublication.metrics.viewers} espectadores
              </Typography>
            </MetricBox>
            
            <MetricBox>
              <Timer sx={{ fontSize: 16 }} />
              <Typography variant="caption">
                {formatDuration(remotePublication.uptime_seconds)}
              </Typography>
            </MetricBox>
          </Box>
        )}

        {/* Error message */}
        {hasError && remotePublication?.last_error && (
          <Box sx={{ mt: 2, p: 1, bgcolor: 'error.light', borderRadius: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <ErrorIcon sx={{ fontSize: 16, color: 'error.dark' }} />
              <Typography variant="caption" color="error.dark">
                {remotePublication.last_error}
              </Typography>
            </Box>
          </Box>
        )}

        {/* Selector de servidor (si no está publicando) */}
        {!isPublishing && availableServers.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              Servidor de destino:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
              {availableServers.map(server => (
                <Chip
                  key={server.id}
                  label={server.name}
                  size="small"
                  variant={server.id === selectedServerId ? 'filled' : 'outlined'}
                  onClick={() => onServerSelect(server.id)}
                  color={server.id === selectedServerId ? 'primary' : 'default'}
                  icon={server.is_authenticated ? <CloudUpload /> : <ErrorIcon />}
                />
              ))}
            </Box>
          </Box>
        )}
      </>
    );
  };

  return (
    <>
      <StyledCard>
        <StatusBar status={remotePublication?.status || PublishingStatus.IDLE} />
        
        {isProcessing && <LinearProgress sx={{ position: 'absolute', top: 4, left: 0, right: 0 }} />}
        
        <CardContent>
          {renderCardContent()}
        </CardContent>

        {/* Métricas expandibles */}
        {isPublishing && remotePublication && (
          <>
            <Divider />
            <CardActions sx={{ justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Métricas detalladas
              </Typography>
              <IconButton
                size="small"
                onClick={() => setExpanded(!expanded)}
                aria-expanded={expanded}
                aria-label="mostrar métricas"
              >
                {expanded ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
            </CardActions>
            
            <Collapse in={expanded} timeout="auto" unmountOnExit>
              <Divider />
              <CardContent>
                <RemoteMetricsDisplay
                  metrics={remotePublication.metrics}
                  uptime={remotePublication.uptime_seconds}
                  publishUrl={remotePublication.publish_url}
                  webrtcUrl={remotePublication.webrtc_url}
                />
              </CardContent>
            </Collapse>
          </>
        )}

        {/* Acciones */}
        <Divider />
        <CardActions sx={{ justifyContent: 'space-between' }}>
          <PublishingControlButton
            cameraId={cameraId}
            cameraName={cameraName}
            status={remotePublication?.status.toLowerCase() as any || 'idle'}
            onStart={handleStart}
            onStop={handleStop}
            disabled={!currentServer || isProcessing}
            showConfirmation={true}
          />
          
          {isPublishing && onOpenViewer && (
            <Tooltip title="Abrir visor WebRTC">
              <IconButton
                color="primary"
                onClick={onOpenViewer}
                size="small"
              >
                <Launch />
              </IconButton>
            </Tooltip>
          )}
        </CardActions>
      </StyledCard>

      {/* Menú de opciones */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        {onRestart && isPublishing && (
          <MenuItem onClick={() => { handleMenuClose(); handleRestart(); }}>
            <ListItemIcon>
              <Refresh fontSize="small" />
            </ListItemIcon>
            <ListItemText>Reiniciar publicación</ListItemText>
          </MenuItem>
        )}
        
        {onConfigure && (
          <MenuItem onClick={() => { handleMenuClose(); onConfigure(); }}>
            <ListItemIcon>
              <Settings fontSize="small" />
            </ListItemIcon>
            <ListItemText>Configurar</ListItemText>
          </MenuItem>
        )}
        
        {remotePublication && (
          <>
            <Divider />
            <MenuItem disabled>
              <ListItemIcon>
                <InfoIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText 
                primary="Información"
                secondary={`ID: ${cameraId}`}
              />
            </MenuItem>
          </>
        )}
      </Menu>
    </>
  );
});

RemotePublishingCard.displayName = 'RemotePublishingCard';