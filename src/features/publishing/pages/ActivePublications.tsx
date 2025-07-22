/**
 * 🎥 Active Publications Page - Universal Camera Viewer
 * Control de publicaciones activas hacia MediaMTX
 */

import React, { useEffect, useState, memo, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Tooltip,
  Button,
  TextField,
  InputAdornment,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Fade,
  alpha
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  HelpOutline as HelpIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import { usePublishingStore } from '../../../stores/publishingStore';
import { useCameraStoreV2 } from '../../../stores/cameraStore.v2';
import { PublishingStatus, STATUS_COLORS, STATUS_LABELS } from '../types';
import { formatDuration, formatBitrate, formatRelativeTime } from '../utils';

/**
 * Página de control de publicaciones activas
 */
const ActivePublications = memo(() => {
  const {
    activePublications,
    isLoading,
    isPublishing,
    startPublishing,
    stopPublishing,
    fetchPublishingStatus,
    getPublicationByCameraId
  } = usePublishingStore();

  const { cameras, loadCameras } = useCameraStoreV2();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedError, setSelectedError] = useState<{ cameraId: string; error: string } | null>(null);
  const [confirmStop, setConfirmStop] = useState<string | null>(null);

  // Cargar datos al montar
  useEffect(() => {
    const loadData = async () => {
      await Promise.all([
        loadCameras(),
        fetchPublishingStatus()
      ]);
    };
    loadData();
  }, [loadCameras, fetchPublishingStatus]);

  // Auto-refresh cada 5 segundos
  useEffect(() => {
    const interval = setInterval(fetchPublishingStatus, 5000);
    return () => clearInterval(interval);
  }, [fetchPublishingStatus]);

  // Manejar inicio de publicación
  const handleStart = useCallback(async (cameraId: string) => {
    try {
      await startPublishing(cameraId);
    } catch (error) {
      console.error('Error al iniciar publicación:', error);
    }
  }, [startPublishing]);

  // Manejar detención de publicación
  const handleStop = useCallback(async (cameraId: string) => {
    setConfirmStop(null);
    try {
      await stopPublishing(cameraId);
    } catch (error) {
      console.error('Error al detener publicación:', error);
    }
  }, [stopPublishing]);

  // Filtrar cámaras por búsqueda
  const filteredCameras = Array.from(cameras.values()).filter(camera => {
    const searchLower = searchQuery.toLowerCase();
    return (
      camera.display_name.toLowerCase().includes(searchLower) ||
      camera.ip_address.includes(searchQuery) ||
      camera.camera_id.toLowerCase().includes(searchLower)
    );
  });

  // Renderizar estado con chip
  const renderStatusChip = (status: PublishingStatus) => (
    <Chip
      label={STATUS_LABELS[status]}
      size="small"
      sx={{
        bgcolor: alpha(STATUS_COLORS[status], 0.2),
        color: STATUS_COLORS[status],
        fontWeight: 500
      }}
    />
  );

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Fade in timeout={300}>
        <Box>
          {/* Header */}
          <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h4" gutterBottom>
                Publicaciones Activas
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Control de streaming hacia servidores MediaMTX
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                size="small"
                placeholder="Buscar cámara..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  )
                }}
                sx={{ width: 250 }}
              />
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={fetchPublishingStatus}
                disabled={isLoading}
              >
                Actualizar
              </Button>
            </Box>
          </Box>

          {/* Tabla de cámaras */}
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Cámara</TableCell>
                  <TableCell>Dirección IP</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      Estado
                      <Tooltip title="Estado actual de la publicación hacia MediaMTX. Verde = Activo, Amarillo = Iniciando, Rojo = Error" arrow placement="top">
                        <HelpIcon sx={{ fontSize: 16, cursor: 'help', color: 'action.disabled' }} />
                      </Tooltip>
                    </Box>
                  </TableCell>
                  <TableCell align="center">
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                      Tiempo Activo
                      <Tooltip title="Tiempo transcurrido desde que se inició la publicación" arrow placement="top">
                        <HelpIcon sx={{ fontSize: 16, cursor: 'help', color: 'action.disabled' }} />
                      </Tooltip>
                    </Box>
                  </TableCell>
                  <TableCell align="center">
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                      FPS
                      <Tooltip title="Frames por segundo actuales. Valores normales: 15-30 FPS" arrow placement="top">
                        <HelpIcon sx={{ fontSize: 16, cursor: 'help', color: 'action.disabled' }} />
                      </Tooltip>
                    </Box>
                  </TableCell>
                  <TableCell align="center">
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                      Bitrate
                      <Tooltip title="Tasa de bits actual del stream. Mayor bitrate = mejor calidad pero más ancho de banda" arrow placement="top">
                        <HelpIcon sx={{ fontSize: 16, cursor: 'help', color: 'action.disabled' }} />
                      </Tooltip>
                    </Box>
                  </TableCell>
                  <TableCell align="center">
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                      Viewers
                      <Tooltip title="Número de clientes conectados viendo este stream en tiempo real" arrow placement="top">
                        <HelpIcon sx={{ fontSize: 16, cursor: 'help', color: 'action.disabled' }} />
                      </Tooltip>
                    </Box>
                  </TableCell>
                  <TableCell align="center">
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                      Errores
                      <Tooltip title="Cantidad de errores ocurridos durante la publicación. Click para ver detalles" arrow placement="top">
                        <WarningIcon sx={{ fontSize: 16, cursor: 'help', color: 'warning.main' }} />
                      </Tooltip>
                    </Box>
                  </TableCell>
                  <TableCell align="center">Acciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredCameras.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                      <Typography variant="body2" color="text.secondary">
                        {searchQuery ? 'No se encontraron cámaras' : 'No hay cámaras registradas'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredCameras.map((camera) => {
                    const publication = getPublicationByCameraId(camera.camera_id);
                    const isTransitioning = isPublishing.get(camera.camera_id) || false;
                    const isActive = publication && (
                      publication.status === PublishingStatus.PUBLISHING ||
                      publication.status === PublishingStatus.STARTING ||
                      publication.status === PublishingStatus.RECONNECTING
                    );

                    return (
                      <TableRow key={camera.camera_id}>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {camera.display_name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {camera.camera_id}
                          </Typography>
                        </TableCell>
                        <TableCell>{camera.ip_address}</TableCell>
                        <TableCell>
                          {publication ? renderStatusChip(publication.status) : (
                            <Chip label="Inactivo" size="small" variant="outlined" />
                          )}
                        </TableCell>
                        <TableCell align="center">
                          {publication && publication.uptime_seconds > 0
                            ? formatDuration(publication.uptime_seconds)
                            : '-'}
                        </TableCell>
                        <TableCell align="center">
                          {publication?.metrics.fps || '-'}
                        </TableCell>
                        <TableCell align="center">
                          {publication?.metrics.bitrate_kbps
                            ? formatBitrate(publication.metrics.bitrate_kbps)
                            : '-'}
                        </TableCell>
                        <TableCell align="center">
                          {publication?.metrics.viewers || '-'}
                        </TableCell>
                        <TableCell align="center">
                          {publication && publication.error_count > 0 ? (
                            <Tooltip title="Ver último error">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => setSelectedError({
                                  cameraId: camera.camera_id,
                                  error: publication.last_error || 'Error desconocido'
                                })}
                              >
                                <ErrorIcon fontSize="small" />
                                <Typography variant="caption" sx={{ ml: 0.5 }}>
                                  {publication.error_count}
                                </Typography>
                              </IconButton>
                            </Tooltip>
                          ) : (
                            <Typography variant="body2" color="text.secondary">
                              0
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell align="center">
                          <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
                            {isActive ? (
                              <Tooltip title="Detener publicación">
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => setConfirmStop(camera.camera_id)}
                                  disabled={isTransitioning}
                                >
                                  {isTransitioning ? (
                                    <CircularProgress size={18} />
                                  ) : (
                                    <StopIcon />
                                  )}
                                </IconButton>
                              </Tooltip>
                            ) : (
                              <Tooltip title="Iniciar publicación">
                                <IconButton
                                  size="small"
                                  color="success"
                                  onClick={() => handleStart(camera.camera_id)}
                                  disabled={isTransitioning}
                                >
                                  {isTransitioning ? (
                                    <CircularProgress size={18} />
                                  ) : (
                                    <PlayIcon />
                                  )}
                                </IconButton>
                              </Tooltip>
                            )}
                            {publication && (
                              <Tooltip title="Ver detalles">
                                <IconButton size="small">
                                  <InfoIcon />
                                </IconButton>
                              </Tooltip>
                            )}
                          </Box>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Diálogo de confirmación */}
          <Dialog
            open={confirmStop !== null}
            onClose={() => setConfirmStop(null)}
            maxWidth="xs"
            fullWidth
          >
            <DialogTitle>Confirmar Detención</DialogTitle>
            <DialogContent>
              <Typography>
                ¿Estás seguro de que deseas detener la publicación de esta cámara?
              </Typography>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setConfirmStop(null)}>
                Cancelar
              </Button>
              <Button
                onClick={() => confirmStop && handleStop(confirmStop)}
                color="error"
                variant="contained"
              >
                Detener
              </Button>
            </DialogActions>
          </Dialog>

          {/* Diálogo de error */}
          <Dialog
            open={selectedError !== null}
            onClose={() => setSelectedError(null)}
            maxWidth="sm"
            fullWidth
          >
            <DialogTitle>Detalles del Error</DialogTitle>
            <DialogContent>
              <Typography variant="body2" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                {selectedError?.error}
              </Typography>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setSelectedError(null)}>
                Cerrar
              </Button>
            </DialogActions>
          </Dialog>
        </Box>
      </Fade>
    </Container>
  );
});

ActivePublications.displayName = 'ActivePublications';

export default ActivePublications;