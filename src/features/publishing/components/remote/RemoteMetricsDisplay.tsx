/**
 * 📊 Remote Metrics Display - Universal Camera Viewer
 * Componente para visualización de métricas de publicación remota
 * 
 * Muestra:
 * - FPS y bitrate con indicadores visuales
 * - Información de viewers y ancho de banda
 * - URLs de publicación y visualización
 * - Tiempo de actividad formateado
 */

import React, { memo } from 'react';
import {
  Box,
  Grid,
  Typography,
  Paper,
  Tooltip,
  IconButton,
  LinearProgress,
  Chip
} from '@mui/material';
import {
  Speed,
  DataUsage,
  People,
  Timer,
  Link as LinkIcon,
  ContentCopy,
  CheckCircle,
  Warning
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { PublishMetrics } from '../../types';
import { formatBytes, formatDuration } from '../../../../utils/formatting';

// === STYLED COMPONENTS ===

const MetricPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(1),
  transition: 'all 0.3s ease',
  '&:hover': {
    boxShadow: theme.shadows[3],
  }
}));

const MetricHeader = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
  marginBottom: theme.spacing(1)
}));

const MetricValue = styled(Typography)(({ theme }) => ({
  fontSize: '1.5rem',
  fontWeight: 600,
  color: theme.palette.text.primary
}));

const UrlBox = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
  padding: theme.spacing(1),
  backgroundColor: theme.palette.grey[100],
  borderRadius: theme.shape.borderRadius,
  fontFamily: 'monospace',
  fontSize: '0.875rem',
  overflow: 'hidden',
  ...theme.applyStyles('dark', {
    backgroundColor: theme.palette.grey[800]
  })
}));

// === INTERFACES ===

interface RemoteMetricsDisplayProps {
  metrics: PublishMetrics;
  uptime?: number;
  publishUrl?: string;
  webrtcUrl?: string;
  showUrls?: boolean;
}

// === HELPERS ===

/**
 * Determina el color basado en el valor de FPS
 */
const getFpsColor = (fps: number): 'success' | 'warning' | 'error' => {
  if (fps >= 25) return 'success';
  if (fps >= 15) return 'warning';
  return 'error';
};

/**
 * Determina el color basado en el bitrate
 */
const getBitrateColor = (bitrate: number): 'success' | 'warning' | 'error' => {
  if (bitrate >= 1000 && bitrate <= 4000) return 'success';
  if (bitrate < 500 || bitrate > 6000) return 'error';
  return 'warning';
};

/**
 * Copia texto al portapapeles
 */
const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    console.error('Error copying to clipboard:', error);
    return false;
  }
};

// === COMPONENTE PRINCIPAL ===

export const RemoteMetricsDisplay = memo<RemoteMetricsDisplayProps>(({
  metrics,
  uptime = 0,
  publishUrl,
  webrtcUrl,
  showUrls = true
}) => {
  const [copiedUrl, setCopiedUrl] = React.useState<string | null>(null);

  const handleCopyUrl = async (url: string, type: 'publish' | 'webrtc') => {
    const success = await copyToClipboard(url);
    if (success) {
      setCopiedUrl(type);
      setTimeout(() => setCopiedUrl(null), 2000);
    }
  };

  return (
    <Box>
      <Grid container spacing={2}>
        {/* FPS */}
        <Grid item xs={6} sm={3}>
          <MetricPaper elevation={1}>
            <MetricHeader>
              <Speed color="action" />
              <Typography variant="body2" color="text.secondary">
                FPS
              </Typography>
            </MetricHeader>
            <MetricValue>
              {metrics.fps}
            </MetricValue>
            <Chip
              label={
                metrics.fps >= 25 ? 'Óptimo' :
                metrics.fps >= 15 ? 'Aceptable' : 'Bajo'
              }
              size="small"
              color={getFpsColor(metrics.fps)}
              variant="outlined"
            />
          </MetricPaper>
        </Grid>

        {/* Bitrate */}
        <Grid item xs={6} sm={3}>
          <MetricPaper elevation={1}>
            <MetricHeader>
              <DataUsage color="action" />
              <Typography variant="body2" color="text.secondary">
                Bitrate
              </Typography>
            </MetricHeader>
            <MetricValue>
              {metrics.bitrate_kbps}
            </MetricValue>
            <Typography variant="caption" color="text.secondary">
              kbps
            </Typography>
            <LinearProgress
              variant="determinate"
              value={Math.min((metrics.bitrate_kbps / 5000) * 100, 100)}
              color={getBitrateColor(metrics.bitrate_kbps)}
              sx={{ mt: 1 }}
            />
          </MetricPaper>
        </Grid>

        {/* Viewers */}
        <Grid item xs={6} sm={3}>
          <MetricPaper elevation={1}>
            <MetricHeader>
              <People color="action" />
              <Typography variant="body2" color="text.secondary">
                Espectadores
              </Typography>
            </MetricHeader>
            <MetricValue>
              {metrics.viewers}
            </MetricValue>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {metrics.viewers > 0 ? (
                <CheckCircle sx={{ fontSize: 16, color: 'success.main' }} />
              ) : (
                <Warning sx={{ fontSize: 16, color: 'warning.main' }} />
              )}
              <Typography variant="caption" color="text.secondary">
                {metrics.viewers > 0 ? 'En vivo' : 'Sin audiencia'}
              </Typography>
            </Box>
          </MetricPaper>
        </Grid>

        {/* Uptime */}
        <Grid item xs={6} sm={3}>
          <MetricPaper elevation={1}>
            <MetricHeader>
              <Timer color="action" />
              <Typography variant="body2" color="text.secondary">
                Tiempo activo
              </Typography>
            </MetricHeader>
            <MetricValue>
              {formatDuration(uptime, 'compact')}
            </MetricValue>
            <Typography variant="caption" color="text.secondary">
              {new Date(Date.now() - uptime * 1000).toLocaleTimeString('es-ES')}
            </Typography>
          </MetricPaper>
        </Grid>

        {/* Estadísticas adicionales */}
        <Grid item xs={12}>
          <MetricPaper elevation={1}>
            <Typography variant="subtitle2" gutterBottom>
              Estadísticas de transmisión
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={4}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Frames enviados
                  </Typography>
                  <Typography variant="body2">
                    {metrics.frames_sent.toLocaleString('es-ES')}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={4}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Datos enviados
                  </Typography>
                  <Typography variant="body2">
                    {formatBytes(metrics.bytes_sent)}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={4}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Bitrate promedio
                  </Typography>
                  <Typography variant="body2">
                    {uptime > 0 
                      ? Math.round((metrics.bytes_sent * 8) / uptime / 1000) 
                      : 0
                    } kbps
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </MetricPaper>
        </Grid>

        {/* URLs de publicación */}
        {showUrls && (publishUrl || webrtcUrl) && (
          <Grid item xs={12}>
            <MetricPaper elevation={1}>
              <Typography variant="subtitle2" gutterBottom>
                URLs de acceso
              </Typography>
              
              {publishUrl && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary" gutterBottom>
                    URL de publicación (RTMP/RTSP)
                  </Typography>
                  <UrlBox>
                    <LinkIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                    <Typography
                      variant="body2"
                      sx={{
                        flex: 1,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      {publishUrl}
                    </Typography>
                    <Tooltip title={copiedUrl === 'publish' ? 'Copiado!' : 'Copiar URL'}>
                      <IconButton
                        size="small"
                        onClick={() => handleCopyUrl(publishUrl, 'publish')}
                        color={copiedUrl === 'publish' ? 'success' : 'default'}
                      >
                        {copiedUrl === 'publish' ? <CheckCircle /> : <ContentCopy />}
                      </IconButton>
                    </Tooltip>
                  </UrlBox>
                </Box>
              )}

              {webrtcUrl && (
                <Box>
                  <Typography variant="caption" color="text.secondary" gutterBottom>
                    URL de visualización (WebRTC)
                  </Typography>
                  <UrlBox>
                    <LinkIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                    <Typography
                      variant="body2"
                      sx={{
                        flex: 1,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      {webrtcUrl}
                    </Typography>
                    <Tooltip title={copiedUrl === 'webrtc' ? 'Copiado!' : 'Copiar URL'}>
                      <IconButton
                        size="small"
                        onClick={() => handleCopyUrl(webrtcUrl, 'webrtc')}
                        color={copiedUrl === 'webrtc' ? 'success' : 'default'}
                      >
                        {copiedUrl === 'webrtc' ? <CheckCircle /> : <ContentCopy />}
                      </IconButton>
                    </Tooltip>
                  </UrlBox>
                </Box>
              )}
            </MetricPaper>
          </Grid>
        )}
      </Grid>
    </Box>
  );
});

RemoteMetricsDisplay.displayName = 'RemoteMetricsDisplay';