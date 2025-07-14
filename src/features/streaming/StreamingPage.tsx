import React, { useState, useCallback } from "react";
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Card, 
  CardContent,
  Chip,
  Button,
  IconButton,
  Tooltip,
  Divider
} from "@mui/material";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowBack as BackIcon,
  PhotoCamera as SnapshotIcon,
  Fullscreen as FullscreenIcon,
  Settings as SettingsIcon,
  Info as InfoIcon,
} from "@mui/icons-material";
import { VideoPlayer } from "./components/VideoPlayer";
import { useStreamingStore } from "../../stores/streamingStore";
import { useCameraStore } from "../../stores/cameraStore";
import { colorTokens } from "../../design-system/tokens";

const StreamingPage: React.FC = () => {
  const { cameraId } = useParams<{ cameraId: string }>();
  const navigate = useNavigate();
  const [showInfo, setShowInfo] = useState(true);
  
  const camera = useCameraStore(state => 
    state.cameras.find(cam => cam.camera_id === cameraId)
  );
  
  const session = useStreamingStore(state => 
    cameraId ? state.activeSessions.get(cameraId) : undefined
  );

  const handleSnapshot = useCallback((imageData: string) => {
    // Crear un enlace de descarga
    const link = document.createElement('a');
    link.href = `data:image/jpeg;base64,${imageData}`;
    link.download = `snapshot_${cameraId}_${new Date().getTime()}.jpg`;
    link.click();
  }, [cameraId]);

  const handleBack = () => {
    navigate('/cameras');
  };

  if (!cameraId) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h5">Cámara no especificada</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <Box 
        sx={{ 
          p: 2, 
          backgroundColor: (theme) => theme.palette.background.paper,
          borderBottom: (theme) => `1px solid ${theme.palette.divider}`,
          display: 'flex',
          alignItems: 'center',
          gap: 2
        }}
      >
        <IconButton onClick={handleBack} size="small">
          <BackIcon />
        </IconButton>
        
        <Typography variant="h6" sx={{ flex: 1 }}>
          {camera?.display_name || `Cámara ${cameraId}`}
        </Typography>
        
        <Chip
          label={camera?.is_connected ? 'Conectada' : 'Desconectada'}
          size="small"
          color={camera?.is_connected ? 'success' : 'default'}
        />
        
        <Tooltip title="Información">
          <IconButton 
            size="small"
            onClick={() => setShowInfo(!showInfo)}
            color={showInfo ? 'primary' : 'default'}
          >
            <InfoIcon />
          </IconButton>
        </Tooltip>
        
        <Tooltip title="Configuración">
          <IconButton size="small">
            <SettingsIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Main Content */}
      <Box sx={{ flex: 1, p: 2, overflow: 'auto' }}>
        <Grid container spacing={2}>
          {/* Video Player */}
          <Grid item xs={12} md={showInfo ? 8 : 12}>
            <Paper 
              sx={{ 
                p: 2, 
                backgroundColor: '#000',
                height: '600px',
                display: 'flex',
                flexDirection: 'column'
              }}
            >
              <VideoPlayer
                cameraId={cameraId}
                width="100%"
                height="100%"
                autoPlay={true}
                showControls={true}
                onSnapshot={handleSnapshot}
              />
            </Paper>
          </Grid>

          {/* Info Panel */}
          {showInfo && (
            <Grid item xs={12} md={4}>
              <Card sx={{ height: '600px', overflow: 'auto' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Información de la Cámara
                  </Typography>
                  
                  <Divider sx={{ my: 2 }} />
                  
                  {/* Camera Details */}
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Detalles
                    </Typography>
                    <Box sx={{ display: 'grid', gap: 1 }}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          IP:
                        </Typography>
                        <Typography variant="body2">
                          {camera?.ip || 'N/A'}
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Marca:
                        </Typography>
                        <Typography variant="body2">
                          {camera?.brand || 'N/A'}
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Modelo:
                        </Typography>
                        <Typography variant="body2">
                          {camera?.model || 'N/A'}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  {/* Stream Metrics */}
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Métricas de Stream
                    </Typography>
                    <Box sx={{ display: 'grid', gap: 1 }}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          FPS:
                        </Typography>
                        <Typography variant="body2">
                          {session?.metrics.current_fps || 0}
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Latencia:
                        </Typography>
                        <Typography variant="body2">
                          {session?.metrics.current_latency_ms || 0} ms
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Ancho de banda:
                        </Typography>
                        <Typography variant="body2">
                          {session?.metrics.bandwidth_kbps || 0} kbps
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Frames totales:
                        </Typography>
                        <Typography variant="body2">
                          {session?.metrics.total_frames || 0}
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Frames perdidos:
                        </Typography>
                        <Typography variant="body2">
                          {session?.metrics.dropped_frames || 0} ({session?.metrics.drop_rate_percent || 0}%)
                        </Typography>
                      </Box>
                    </Box>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  {/* Capabilities */}
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Capacidades
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {camera?.capabilities?.map(cap => (
                        <Chip
                          key={cap}
                          label={cap}
                          size="small"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      </Box>
    </Box>
  );
};

export default StreamingPage;
