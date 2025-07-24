/**
 * 🎥 Active Publications Unified Page - Universal Camera Viewer
 * Control unificado de publicaciones locales y remotas hacia MediaMTX
 * 
 * @todo Funcionalidades pendientes:
 * - Implementar visor de stream WebRTC inline para publicaciones remotas
 * - Agregar botón de "Ver detalles" con métricas avanzadas
 * - Implementar exportación de métricas a CSV
 * - Agregar soporte para múltiples publicaciones por cámara
 * - Implementar filtros avanzados (por estado, fecha, etc.)
 * 
 * @note Esta página reemplaza a ActivePublications.tsx con una vista unificada
 */

import { useEffect, useState, memo, useCallback } from 'react';
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
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Error as ErrorIcon,
  Computer as LocalIcon,
  CloudQueue as CloudIcon,
  RestartAlt as RestartIcon,
} from '@mui/icons-material';
import { usePublishingStore } from '../../../stores/publishingStore';
import { useCameraStoreV2 } from '../../../stores/cameraStore.v2';
import { formatDuration, formatBitrate } from '../utils';
import { publishingUnifiedService } from '../../../services/publishing/publishingUnifiedService';
import { RemoteServerSelector } from '../components/remote/RemoteServerSelector';
import type { UnifiedPublication, PublicationType } from '../../../services/publishing/publishingUnifiedService';

/**
 * Página unificada de control de publicaciones activas
 */
const ActivePublicationsUnified = memo(() => {
  const {
    remote,
    unifiedMetrics,
    isLoading,
    isPublishing,
    startPublishing,
    stopPublishing,
    startRemotePublishing,
    stopRemotePublishing,
    fetchUnifiedPublications,
    fetchRemoteServers,
  } = usePublishingStore();

  const { cameras, loadCameras } = useCameraStoreV2();

  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<PublicationType | 'all'>('all');
  const [serverFilter, setServerFilter] = useState<number | 'all'>('all');
  const [unifiedPublications, setUnifiedPublications] = useState<UnifiedPublication[]>([]);
  const [selectedCameraForRemote, setSelectedCameraForRemote] = useState<string | null>(null);
  const [selectedServerId, setSelectedServerId] = useState<number | null>(null);
  const [confirmStop, setConfirmStop] = useState<{ cameraId: string; type: PublicationType } | null>(null);
  const [selectedError, setSelectedError] = useState<{ cameraId: string; error: string } | null>(null);

  // Cargar datos al montar
  useEffect(() => {
    const loadData = async () => {
      await Promise.all([
        loadCameras(),
        fetchRemoteServers(),
        fetchUnifiedPublications()
      ]);
    };
    loadData();
  }, [loadCameras, fetchRemoteServers, fetchUnifiedPublications]);

  // Auto-refresh cada 5 segundos
  useEffect(() => {
    const interval = setInterval(fetchUnifiedPublications, 5000);
    return () => clearInterval(interval);
  }, [fetchUnifiedPublications]);

  // Cargar publicaciones unificadas cuando cambien los filtros
  useEffect(() => {
    const loadUnifiedData = async () => {
      try {
        const publications = await publishingUnifiedService.getAllPublications({
          type: typeFilter === 'all' ? undefined : typeFilter,
          server_id: serverFilter === 'all' ? undefined : serverFilter,
          search: searchQuery || undefined,
        });
        setUnifiedPublications(publications);
      } catch (error) {
        console.error('Error cargando publicaciones:', error);
      }
    };
    loadUnifiedData();
  }, [typeFilter, serverFilter, searchQuery]);

  // Manejar inicio de publicación local
  const handleStartLocal = useCallback(async (cameraId: string) => {
    try {
      await startPublishing(cameraId);
    } catch (error) {
      console.error('Error al iniciar publicación local:', error);
    }
  }, [startPublishing]);

  // Manejar inicio de publicación remota
  const handleStartRemote = useCallback(async (cameraId: string, serverId: number) => {
    try {
      await startRemotePublishing(cameraId, serverId);
      setSelectedCameraForRemote(null);
      setSelectedServerId(null);
    } catch (error) {
      console.error('Error al iniciar publicación remota:', error);
    }
  }, [startRemotePublishing]);

  // Manejar detención de publicación
  const handleStop = useCallback(async (cameraId: string, type: PublicationType) => {
    setConfirmStop(null);
    try {
      if (type === 'local') {
        await stopPublishing(cameraId);
      } else {
        await stopRemotePublishing(cameraId);
      }
    } catch (error) {
      console.error('Error al detener publicación:', error);
    }
  }, [stopPublishing, stopRemotePublishing]);

  // Manejar reinicio de publicación
  const handleRestart = useCallback(async (pub: UnifiedPublication) => {
    try {
      await publishingUnifiedService.restartPublication(
        pub.camera_id,
        pub.publication_type,
        pub.server_id
      );
    } catch (error) {
      console.error('Error al reiniciar publicación:', error);
    }
  }, []);

  // Renderizar chip de estado
  const renderStatusChip = (status: string) => {
    const colorMap: Record<string, 'success' | 'error' | 'warning' | 'default'> = {
      publishing: 'success',
      error: 'error',
      stopped: 'default',
      starting: 'warning',
      stopping: 'warning',
    };

    return (
      <Chip
        label={status.charAt(0).toUpperCase() + status.slice(1)}
        size="small"
        color={colorMap[status] || 'default'}
      />
    );
  };

  // Obtener cámaras disponibles para publicación
  const availableCameras = Array.from(cameras.values()).filter(camera => {
    // Filtrar cámaras que no están publicando
    return !unifiedPublications.some(pub => 
      pub.camera_id === camera.camera_id && 
      (pub.status === 'publishing' || pub.status === 'starting')
    );
  });

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Fade in timeout={300}>
        <Box>
          {/* Header */}
          <Box sx={{ mb: 4 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Box>
                <Typography variant="h4" gutterBottom>
                  Publicaciones Activas
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Control unificado de streaming hacia servidores MediaMTX locales y remotos
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Chip
                    icon={<LocalIcon />}
                    label={`${unifiedMetrics.localPublications} locales`}
                    color="primary"
                    variant="outlined"
                  />
                  <Chip
                    icon={<CloudIcon />}
                    label={`${unifiedMetrics.remotePublications} remotas`}
                    color="secondary"
                    variant="outlined"
                  />
                </Box>
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={fetchUnifiedPublications}
                  disabled={isLoading}
                >
                  Actualizar
                </Button>
              </Box>
            </Box>

            {/* Filtros */}
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel>Tipo</InputLabel>
                <Select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value as PublicationType | 'all')}
                  label="Tipo"
                >
                  <MenuItem value="all">Todos</MenuItem>
                  <MenuItem value="local">
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LocalIcon fontSize="small" />
                      Local
                    </Box>
                  </MenuItem>
                  <MenuItem value="remote">
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <CloudIcon fontSize="small" />
                      Remoto
                    </Box>
                  </MenuItem>
                </Select>
              </FormControl>

              {remote.servers.length > 0 && (
                <FormControl size="small" sx={{ minWidth: 200 }}>
                  <InputLabel>Servidor</InputLabel>
                  <Select
                    value={serverFilter}
                    onChange={(e) => setServerFilter(e.target.value as number | 'all')}
                    label="Servidor"
                  >
                    <MenuItem value="all">Todos los servidores</MenuItem>
                    {remote.servers.map(server => (
                      <MenuItem key={server.id} value={server.id}>
                        {server.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}

              <TextField
                size="small"
                placeholder="Buscar cámara..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                slotProps={{
                  input: {
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon fontSize="small" />
                      </InputAdornment>
                    )
                  }
                }}
                sx={{ flexGrow: 1, maxWidth: 400 }}
              />
            </Box>
          </Box>

          {/* Resumen de métricas */}
          <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
            <Paper sx={{ p: 2, flex: 1 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Total Publicaciones
              </Typography>
              <Typography variant="h4">
                {unifiedMetrics.totalPublications}
              </Typography>
            </Paper>
            <Paper sx={{ p: 2, flex: 1 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Viewers Totales
              </Typography>
              <Typography variant="h4">
                {unifiedMetrics.totalViewers}
              </Typography>
            </Paper>
            <Paper sx={{ p: 2, flex: 1 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Ancho de Banda Total
              </Typography>
              <Typography variant="h4">
                {unifiedMetrics.totalBandwidthMbps.toFixed(1)} Mbps
              </Typography>
            </Paper>
          </Box>

          {/* Tabla de publicaciones */}
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Cámara</TableCell>
                  <TableCell>IP / Servidor</TableCell>
                  <TableCell>Tipo</TableCell>
                  <TableCell>Estado</TableCell>
                  <TableCell align="center">Tiempo Activo</TableCell>
                  <TableCell align="center">FPS</TableCell>
                  <TableCell align="center">Bitrate</TableCell>
                  <TableCell align="center">Viewers</TableCell>
                  <TableCell align="center">Acciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {unifiedPublications.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center" sx={{ py: 6 }}>
                      <Typography variant="body1" color="text.secondary">
                        {searchQuery || typeFilter !== 'all' || serverFilter !== 'all' 
                          ? 'No se encontraron publicaciones con los filtros aplicados' 
                          : 'No hay publicaciones activas'}
                      </Typography>
                      {availableCameras.length > 0 && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            {availableCameras.length} cámaras disponibles para publicar
                          </Typography>
                          <Button
                            variant="contained"
                            startIcon={<PlayIcon />}
                            onClick={() => {
                              if (availableCameras.length > 0) {
                                handleStartLocal(availableCameras[0].camera_id);
                              }
                            }}
                          >
                            Iniciar Primera Publicación
                          </Button>
                        </Box>
                      )}
                    </TableCell>
                  </TableRow>
                ) : (
                  unifiedPublications.map((publication) => {
                    const isTransitioning = isPublishing.get(publication.camera_id) || false;
                    const isActive = publication.status === 'publishing' || publication.status === 'starting';

                    return (
                      <TableRow key={`${publication.camera_id}-${publication.publication_type}`}>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                              {publication.camera_name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {publication.camera_id}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box>
                            <Typography variant="body2">
                              {publication.camera_ip}
                            </Typography>
                            {publication.server_name && (
                              <Typography variant="caption" color="text.secondary">
                                {publication.server_name}
                              </Typography>
                            )}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip
                            icon={publication.publication_type === 'local' ? <LocalIcon /> : <CloudIcon />}
                            label={publication.publication_type === 'local' ? 'Local' : 'Remoto'}
                            size="small"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          {renderStatusChip(publication.status)}
                        </TableCell>
                        <TableCell align="center">
                          {publication.metrics.uptime_seconds > 0
                            ? formatDuration(publication.metrics.uptime_seconds)
                            : '-'}
                        </TableCell>
                        <TableCell align="center">
                          {publication.metrics.fps || '-'}
                        </TableCell>
                        <TableCell align="center">
                          {publication.metrics.bitrate_kbps
                            ? formatBitrate(publication.metrics.bitrate_kbps)
                            : '-'}
                        </TableCell>
                        <TableCell align="center">
                          {publication.metrics.viewers || '-'}
                        </TableCell>
                        <TableCell align="center">
                          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 0.5 }}>
                            {isActive ? (
                              <>
                                <Tooltip title="Detener publicación">
                                  <IconButton
                                    size="small"
                                    color="error"
                                    onClick={() => setConfirmStop({ 
                                      cameraId: publication.camera_id, 
                                      type: publication.publication_type 
                                    })}
                                    disabled={isTransitioning}
                                  >
                                    {isTransitioning ? (
                                      <CircularProgress size={18} />
                                    ) : (
                                      <StopIcon />
                                    )}
                                  </IconButton>
                                </Tooltip>
                                <Tooltip title="Reiniciar publicación">
                                  <IconButton
                                    size="small"
                                    color="warning"
                                    onClick={() => handleRestart(publication)}
                                    disabled={isTransitioning}
                                  >
                                    <RestartIcon />
                                  </IconButton>
                                </Tooltip>
                              </>
                            ) : (
                              <Tooltip title={`Iniciar publicación ${publication.publication_type}`}>
                                <IconButton
                                  size="small"
                                  color="success"
                                  onClick={() => {
                                    if (publication.publication_type === 'local') {
                                      handleStartLocal(publication.camera_id);
                                    } else {
                                      setSelectedCameraForRemote(publication.camera_id);
                                    }
                                  }}
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
                            {publication.status === 'error' && publication.error_message && (
                              <Tooltip title={publication.error_message}>
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => setSelectedError({
                                    cameraId: publication.camera_id,
                                    error: publication.error_message || 'Error desconocido'
                                  })}
                                >
                                  <ErrorIcon />
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

          {/* Diálogo de selección de servidor remoto */}
          <Dialog
            open={selectedCameraForRemote !== null}
            onClose={() => {
              setSelectedCameraForRemote(null);
              setSelectedServerId(null);
            }}
            maxWidth="sm"
            fullWidth
          >
            <DialogTitle>Seleccionar Servidor Remoto</DialogTitle>
            <DialogContent>
              <Box sx={{ py: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Selecciona un servidor MediaMTX remoto para publicar la cámara
                </Typography>
                {remote.servers.filter(s => s.is_authenticated).length === 0 ? (
                  <Alert severity="warning" sx={{ mt: 2 }}>
                    No hay servidores remotos autenticados. Primero debes autenticarte con un servidor.
                  </Alert>
                ) : (
                  <RemoteServerSelector
                    servers={remote.servers.filter(s => s.is_authenticated)}
                    selectedServerId={selectedServerId || undefined}
                    onChange={setSelectedServerId}
                    showOnlyAuthenticated
                  />
                )}
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => {
                setSelectedCameraForRemote(null);
                setSelectedServerId(null);
              }}>
                Cancelar
              </Button>
              <Button
                onClick={() => {
                  if (selectedCameraForRemote && selectedServerId) {
                    handleStartRemote(selectedCameraForRemote, selectedServerId);
                  }
                }}
                variant="contained"
                disabled={!selectedServerId}
              >
                Iniciar Publicación
              </Button>
            </DialogActions>
          </Dialog>

          {/* Diálogo de confirmación de detención */}
          <Dialog
            open={confirmStop !== null}
            onClose={() => setConfirmStop(null)}
            maxWidth="xs"
            fullWidth
          >
            <DialogTitle>Confirmar Detención</DialogTitle>
            <DialogContent>
              <Typography>
                ¿Estás seguro de que deseas detener la publicación {confirmStop?.type} de esta cámara?
              </Typography>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setConfirmStop(null)}>
                Cancelar
              </Button>
              <Button
                onClick={() => {
                  if (confirmStop) {
                    handleStop(confirmStop.cameraId, confirmStop.type);
                  }
                }}
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
            <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <ErrorIcon color="error" />
              Error de Publicación
            </DialogTitle>
            <DialogContent>
              <Typography variant="body2" gutterBottom>
                <strong>Cámara:</strong> {selectedError?.cameraId}
              </Typography>
              <Typography variant="body2" color="error">
                <strong>Error:</strong> {selectedError?.error}
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

ActivePublicationsUnified.displayName = 'ActivePublicationsUnified';

export default ActivePublicationsUnified;