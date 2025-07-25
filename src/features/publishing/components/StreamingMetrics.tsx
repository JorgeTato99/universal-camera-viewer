/**
 * Componente para mostrar métricas de streaming en tiempo real
 * 
 * Muestra FPS, bitrate, frames enviados/perdidos y duración del stream
 * con actualización automática cada 2 segundos.
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  CircularProgress,
  IconButton,
  Tooltip,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  Speed as SpeedIcon,
  Memory as BitrateIcon,
  Timer as TimerIcon,
  Assessment as FramesIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  RestartAlt as RestartIcon,
} from '@mui/icons-material';
import { PublishMetrics } from '../types';
import { publishingUnifiedService } from '../../../services/publishing/publishingUnifiedService';
import { colorTokens } from '../../../design-system/tokens';

interface StreamingMetricsProps {
  cameraId: string;
  publicationId: string;
  onRestart?: () => void;
  onStop?: () => void;
  showControls?: boolean;
}

export const StreamingMetrics: React.FC<StreamingMetricsProps> = ({
  cameraId,
  publicationId,
  onRestart,
  onStop,
  showControls = true,
}) => {
  const [metrics, setMetrics] = useState<PublishMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Función para obtener métricas
  const fetchMetrics = async () => {
    try {
      setError(null);
      const data = await publishingUnifiedService.getPublicationMetrics(
        cameraId,
        publicationId
      );
      
      if (data) {
        setMetrics(data as PublishMetrics);
        setLoading(false);
      } else {
        setError('No se pudieron obtener métricas');
      }
    } catch (err) {
      setError('Error al obtener métricas');
      console.error('Error fetching metrics:', err);
    }
  };

  // Actualización automática cada 2 segundos
  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 2000);
    
    return () => clearInterval(interval);
  }, [cameraId, publicationId]);

  // Función para reiniciar manualmente
  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchMetrics();
    setRefreshing(false);
  };

  // Función para reiniciar streaming
  const handleRestart = async () => {
    if (!onRestart) return;
    
    try {
      await publishingUnifiedService.restartPublication(cameraId, publicationId);
      onRestart();
    } catch (err) {
      console.error('Error restarting stream:', err);
    }
  };

  // Formatear duración
  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  // Calcular calidad del stream
  const getStreamQuality = (): { label: string; color: string } => {
    if (!metrics) return { label: 'Desconocido', color: 'default' };
    
    const droppedRatio = metrics.frames_sent > 0 
      ? (metrics.frames_dropped || 0) / metrics.frames_sent 
      : 0;
    
    if (droppedRatio > 0.05) return { label: 'Pobre', color: 'error' };
    if (droppedRatio > 0.02) return { label: 'Regular', color: 'warning' };
    if (metrics.fps < 20) return { label: 'Regular', color: 'warning' };
    
    return { label: 'Excelente', color: 'success' };
  };

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error && !metrics) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error" action={
            <IconButton size="small" onClick={handleRefresh}>
              <RefreshIcon />
            </IconButton>
          }>
            {error}
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const quality = getStreamQuality();
  const droppedPercentage = metrics && metrics.frames_sent > 0
    ? ((metrics.frames_dropped || 0) / metrics.frames_sent * 100).toFixed(1)
    : '0';

  return (
    <Card>
      <CardContent>
        <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" component="div">
            Métricas de Streaming
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip 
              label={quality.label} 
              color={quality.color as any} 
              size="small" 
              icon={metrics?.is_running ? <PlayIcon /> : <StopIcon />}
            />
            {showControls && (
              <>
                <Tooltip title="Actualizar">
                  <span>
                    <IconButton size="small" onClick={handleRefresh} disabled={refreshing}>
                      <RefreshIcon fontSize="small" />
                    </IconButton>
                  </span>
                </Tooltip>
                <Tooltip title="Reiniciar Stream">
                  <span>
                    <IconButton 
                      size="small" 
                      onClick={handleRestart}
                      disabled={!metrics?.is_running}
                      color="warning"
                    >
                      <RestartIcon fontSize="small" />
                    </IconButton>
                  </span>
                </Tooltip>
                {onStop && (
                  <Tooltip title="Detener Stream">
                    <span>
                      <IconButton 
                        size="small" 
                        onClick={onStop}
                        disabled={!metrics?.is_running}
                        color="error"
                      >
                        <StopIcon fontSize="small" />
                      </IconButton>
                    </span>
                  </Tooltip>
                )}
              </>
            )}
          </Box>
        </Box>

        {metrics ? (
          <Grid container spacing={3}>
            {/* FPS */}
            <Grid size={{ xs: 6, md: 3 }}>
              <Box sx={{ textAlign: 'center' }}>
                <SpeedIcon sx={{ fontSize: 40, color: colorTokens.primary[500], mb: 1 }} />
                <Typography variant="h4" component="div">
                  {metrics.fps.toFixed(1)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  FPS
                </Typography>
              </Box>
            </Grid>

            {/* Bitrate */}
            <Grid size={{ xs: 6, md: 3 }}>
              <Box sx={{ textAlign: 'center' }}>
                <BitrateIcon sx={{ fontSize: 40, color: colorTokens.primary[400], mb: 1 }} />
                <Typography variant="h4" component="div">
                  {metrics.bitrate_kbps}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Kbps
                </Typography>
              </Box>
            </Grid>

            {/* Duración */}
            <Grid size={{ xs: 6, md: 3 }}>
              <Box sx={{ textAlign: 'center' }}>
                <TimerIcon sx={{ fontSize: 40, color: colorTokens.secondary[500], mb: 1 }} />
                <Typography variant="h4" component="div">
                  {formatDuration(metrics.duration_seconds || 0)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Duración
                </Typography>
              </Box>
            </Grid>

            {/* Frames */}
            <Grid size={{ xs: 6, md: 3 }}>
              <Box sx={{ textAlign: 'center' }}>
                <FramesIcon sx={{ fontSize: 40, color: colorTokens.status.connecting, mb: 1 }} />
                <Typography variant="h4" component="div">
                  {metrics.frames_sent}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Frames ({droppedPercentage}% perdidos)
                </Typography>
              </Box>
            </Grid>
          </Grid>
        ) : (
          <Typography variant="body2" color="text.secondary" align="center">
            No hay métricas disponibles
          </Typography>
        )}

        {/* Barra de progreso para frames perdidos */}
        {metrics && metrics.frames_sent > 0 && (
          <Box sx={{ mt: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Calidad del Stream
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {100 - parseFloat(droppedPercentage)}% sin pérdidas
              </Typography>
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={100 - parseFloat(droppedPercentage)} 
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: colorTokens.neutral[200],
                '& .MuiLinearProgress-bar': {
                  backgroundColor: 
                    parseFloat(droppedPercentage) > 5 ? colorTokens.status.error :
                    parseFloat(droppedPercentage) > 2 ? colorTokens.status.connecting :
                    colorTokens.status.connected
                }
              }}
            />
          </Box>
        )}

        {/* TODO: Implementar gráficas en tiempo real cuando esté disponible */}
        {/* <Box sx={{ mt: 3 }}>
          <Typography variant="caption" color="text.secondary">
            * Gráficas en tiempo real próximamente
          </Typography>
        </Box> */}
      </CardContent>
    </Card>
  );
};