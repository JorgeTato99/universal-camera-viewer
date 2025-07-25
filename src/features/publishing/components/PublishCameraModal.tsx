/**
 * 🎥 Publish Camera Modal - Universal Camera Viewer
 * Modal para seleccionar y publicar cámaras locales a servidores MediaMTX remotos
 * 
 * Características:
 * - Lista de cámaras locales con estado en tiempo real
 * - Selector de servidor remoto con validación de autenticación
 * - Preview de la cámara seleccionada (TODO: Implementar preview)
 * - Validación de conectividad antes de publicar
 * - Feedback visual del proceso de publicación
 * 
 * @todo Funcionalidades pendientes:
 * - Implementar preview en vivo de la cámara seleccionada
 * - Agregar opción de configuración avanzada (resolución, bitrate)
 * - Permitir publicación simultánea a múltiples servidores
 * - Agregar validación de ancho de banda disponible
 */

import React, { useState, useCallback, useEffect, useMemo } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Card,
  CardContent,
  CardActionArea,
  Chip,
  CircularProgress,
  Alert,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Skeleton,
  alpha,
} from '@mui/material';
import {
  Close as CloseIcon,
  Videocam as CameraIcon,
  VideocamOff as CameraOffIcon,
  CloudQueue as CloudIcon,
  CheckCircle as CheckIcon,
  PlayArrow as PlayIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import { useCameraStoreV2 } from '../../../stores/cameraStore.v2';
import { usePublishingStore } from '../../../stores/publishingStore';
import { notificationStore } from '../../../stores/notificationStore';
import { colorTokens } from '../../../design-system/tokens';
import { ConnectionStatus } from '../../../types/camera.types.v2';

// === TIPOS Y CONSTANTES ===

interface PublishCameraModalProps {
  open: boolean;
  onClose: () => void;
  onPublishSuccess?: (cameraId: string, serverId: number) => void;
}

const STEPS = ['Seleccionar Cámara', 'Elegir Servidor', 'Confirmar y Publicar'];

// === COMPONENTE PRINCIPAL ===

export const PublishCameraModal: React.FC<PublishCameraModalProps> = ({
  open,
  onClose,
  onPublishSuccess,
}) => {
  // Estado del componente
  const [activeStep, setActiveStep] = useState(0);
  const [selectedCameraId, setSelectedCameraId] = useState<string | null>(null);
  const [selectedServerId, setSelectedServerId] = useState<number | null>(null);
  const [isPublishing, setIsPublishing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Stores
  const { cameras, loadCameras, isLoading: isLoadingCameras } = useCameraStoreV2();
  const { 
    remote, 
    fetchRemoteServers, 
    startRemotePublishing
  } = usePublishingStore();

  // Cargar datos al abrir el modal
  useEffect(() => {
    if (open) {
      loadCameras();
      fetchRemoteServers();
      // Reset estado
      setActiveStep(0);
      setSelectedCameraId(null);
      setSelectedServerId(null);
      setError(null);
    }
  }, [open, loadCameras, fetchRemoteServers]);

  // Obtener cámaras disponibles (no publicadas y online)
  const availableCameras = useMemo(() => {
    return Array.from(cameras.values()).filter(camera => {
      // TODO: Implementar filtrado de cámaras ya publicadas
      // Necesita integración con el estado de publicaciones activas
      // para evitar publicar la misma cámara dos veces
      // Pseudocódigo:
      // const isAlreadyPublishing = publishingMap.has(camera.camera_id);
      // return camera.status === ConnectionStatus.CONNECTED && !isAlreadyPublishing;
      
      // Por ahora, mostrar todas las cámaras con estado 'connected'
      return camera.status === ConnectionStatus.CONNECTED;
    });
  }, [cameras]);

  // Obtener servidores autenticados
  const authenticatedServers = useMemo(() => {
    return remote.servers.filter(server => server.is_authenticated);
  }, [remote.servers]);

  // Auto-seleccionar servidor si solo hay uno
  useEffect(() => {
    if (authenticatedServers.length === 1 && !selectedServerId) {
      setSelectedServerId(authenticatedServers[0].id);
    }
  }, [authenticatedServers, selectedServerId]);

  // Handlers
  const handleCameraSelect = useCallback((cameraId: string) => {
    setSelectedCameraId(cameraId);
    setError(null);
    if (activeStep === 0) {
      setActiveStep(1);
    }
  }, [activeStep]);

  const handleServerSelect = useCallback((serverId: number) => {
    setSelectedServerId(serverId);
    setError(null);
    if (activeStep === 1) {
      setActiveStep(2);
    }
  }, [activeStep]);

  const handlePublish = async () => {
    if (!selectedCameraId || !selectedServerId) {
      setError('Debes seleccionar una cámara y un servidor');
      return;
    }

    setIsPublishing(true);
    setError(null);

    try {
      await startRemotePublishing(selectedCameraId, selectedServerId);
      
      notificationStore.addNotification({
        type: 'success',
        title: 'Publicación iniciada',
        message: 'La cámara se está publicando al servidor remoto',
      });

      onPublishSuccess?.(selectedCameraId, selectedServerId);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Error al iniciar la publicación');
      notificationStore.addNotification({
        type: 'error',
        title: 'Error al publicar',
        message: err.message || 'No se pudo iniciar la publicación',
      });
    } finally {
      setIsPublishing(false);
    }
  };

  const handleBack = () => {
    if (activeStep > 0) {
      setActiveStep(activeStep - 1);
    }
  };


  // Obtener datos seleccionados
  const selectedCamera = selectedCameraId ? cameras.get(selectedCameraId) : null;
  const selectedServer = selectedServerId 
    ? remote.servers.find(s => s.id === selectedServerId) 
    : null;

  // Renderizar contenido del paso actual
  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return renderCameraSelection();
      case 1:
        return renderServerSelection();
      case 2:
        return renderConfirmation();
      default:
        return null;
    }
  };

  // Renderizar selección de cámaras
  const renderCameraSelection = () => {
    if (isLoadingCameras) {
      return (
        <Box sx={{ pt: 2 }}>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
            {[1, 2, 3].map((i) => (
              <Box key={i} sx={{ 
                width: { xs: '100%', sm: 'calc(50% - 8px)', md: 'calc(33.333% - 11px)' }
              }}>
                <Skeleton variant="rectangular" height={120} />
              </Box>
            ))}
          </Box>
        </Box>
      );
    }

    if (availableCameras.length === 0) {
      return (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <CameraOffIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No hay cámaras disponibles
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Asegúrate de tener cámaras conectadas y en línea
          </Typography>
          <Button
            startIcon={<RefreshIcon />}
            onClick={loadCameras}
            sx={{ mt: 2 }}
          >
            Actualizar
          </Button>
        </Box>
      );
    }

    return (
      <Box sx={{ pt: 2 }}>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Selecciona la cámara que deseas publicar:
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 1 }}>
          {availableCameras.map((camera) => (
            <Box key={camera.camera_id} sx={{ 
              width: { xs: '100%', sm: 'calc(50% - 8px)', md: 'calc(33.333% - 11px)' }
            }}>
              <Card 
                variant={selectedCameraId === camera.camera_id ? 'elevation' : 'outlined'}
                sx={{ 
                  position: 'relative',
                  border: selectedCameraId === camera.camera_id 
                    ? `2px solid ${colorTokens.primary[500]}` 
                    : undefined,
                  transition: 'all 0.2s',
                }}
              >
                <CardActionArea onClick={() => handleCameraSelect(camera.camera_id)}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'start', gap: 2 }}>
                      <CameraIcon 
                        sx={{ 
                          fontSize: 40, 
                          color: camera.status === ConnectionStatus.CONNECTED 
                            ? colorTokens.status.connected 
                            : 'text.disabled' 
                        }} 
                      />
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          {camera.display_name || camera.model || 'Cámara sin nombre'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" display="block">
                          {camera.ip_address}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 0.5, mt: 1 }}>
                          <Chip 
                            label={camera.brand} 
                            size="small" 
                            variant="outlined" 
                          />
                          {camera.status === ConnectionStatus.CONNECTED && (
                            <Chip 
                              label="En línea" 
                              size="small" 
                              color="success" 
                              icon={<CheckIcon />}
                            />
                          )}
                        </Box>
                      </Box>
                    </Box>
                  </CardContent>
                </CardActionArea>
                {selectedCameraId === camera.camera_id && (
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 8,
                      right: 8,
                      bgcolor: colorTokens.primary[500],
                      color: 'white',
                      borderRadius: '50%',
                      p: 0.5,
                    }}
                  >
                    <CheckIcon fontSize="small" />
                  </Box>
                )}
              </Card>
            </Box>
          ))}
        </Box>
      </Box>
    );
  };

  // Renderizar selección de servidor
  const renderServerSelection = () => {
    if (remote.isLoadingServers) {
      return (
        <Box sx={{ pt: 2 }}>
          <Skeleton variant="rectangular" height={200} />
        </Box>
      );
    }

    if (authenticatedServers.length === 0) {
      return (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <CloudIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No hay servidores autenticados
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Debes autenticarte en al menos un servidor MediaMTX remoto
          </Typography>
          <Button
            variant="contained"
            startIcon={<CloudIcon />}
            onClick={onClose}
            sx={{ mt: 2 }}
          >
            Configurar Servidores
          </Button>
        </Box>
      );
    }

    return (
      <Box sx={{ pt: 2 }}>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Selecciona el servidor donde se publicará la cámara:
        </Typography>
        
        {authenticatedServers.length === 1 ? (
          <Alert severity="info" sx={{ mt: 2 }}>
            Se ha seleccionado automáticamente el único servidor disponible
          </Alert>
        ) : null}

        <FormControl fullWidth sx={{ mt: 2 }}>
          <InputLabel>Servidor MediaMTX</InputLabel>
          <Select
            value={selectedServerId || ''}
            onChange={(e) => handleServerSelect(Number(e.target.value))}
            label="Servidor MediaMTX"
          >
            {authenticatedServers.map((server) => (
              <MenuItem key={server.id} value={server.id}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                  <CloudIcon />
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="body2">{server.name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {server.api_url}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Chip 
                      label="Autenticado" 
                      size="small" 
                      color="success" 
                      icon={<SecurityIcon />}
                    />
                    {server.is_active && (
                      <Chip label="Activo" size="small" color="primary" />
                    )}
                  </Box>
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {selectedServer && (
          <Box sx={{ mt: 3, p: 2, bgcolor: alpha(colorTokens.primary[500], 0.08), borderRadius: 1 }}>
            <Typography variant="subtitle2" gutterBottom>
              Detalles del servidor:
            </Typography>
            <Typography variant="body2" color="text.secondary">
              URL de API: {selectedServer.api_url}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              URL de RTSP: {selectedServer.rtsp_url}
            </Typography>
            {selectedServer.last_health_check && (
              <Typography variant="body2" color="text.secondary">
                Última verificación: {new Date(selectedServer.last_health_check).toLocaleString()}
              </Typography>
            )}
          </Box>
        )}
      </Box>
    );
  };

  // Renderizar confirmación
  const renderConfirmation = () => {
    if (!selectedCamera || !selectedServer) {
      return null;
    }

    return (
      <Box sx={{ pt: 2 }}>
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            La cámara se publicará en internet a través del servidor MediaMTX remoto.
            El streaming comenzará inmediatamente después de confirmar.
          </Typography>
        </Alert>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Resumen de cámara */}
          <Box>
            <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CameraIcon /> Cámara seleccionada
            </Typography>
            <Box sx={{ pl: 4 }}>
              <Typography variant="body2">
                {selectedCamera.display_name || selectedCamera.model}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                IP: {selectedCamera.ip_address} • {selectedCamera.brand}
              </Typography>
            </Box>
          </Box>

          <Divider />

          {/* Resumen de servidor */}
          <Box>
            <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CloudIcon /> Servidor de destino
            </Typography>
            <Box sx={{ pl: 4 }}>
              <Typography variant="body2">
                {selectedServer.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {selectedServer.api_url}
              </Typography>
            </Box>
          </Box>

          <Divider />

          {/* Información adicional */}
          <Box>
            <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <InfoIcon /> Información importante
            </Typography>
            <Box sx={{ pl: 4 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                • El streaming consumirá ancho de banda de tu conexión
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                • La cámara será accesible desde internet
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • Puedes detener la publicación en cualquier momento
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* TODO: Agregar preview de la cámara aquí */}
        <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1, textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            Preview de la cámara disponible próximamente
          </Typography>
        </Box>
      </Box>
    );
  };

  return (
    <Dialog
      open={open}
      onClose={isPublishing ? undefined : onClose}
      maxWidth="md"
      fullWidth
      disableEscapeKeyDown={isPublishing}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6">
            Publicar Cámara a Servidor Remoto
          </Typography>
          <IconButton
            onClick={onClose}
            disabled={isPublishing}
            size="small"
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Stepper activeStep={activeStep} orientation="vertical">
          {STEPS.map((label, index) => (
            <Step key={label}>
              <StepLabel
                optional={
                  index === 0 && selectedCamera ? (
                    <Typography variant="caption">{selectedCamera.display_name}</Typography>
                  ) : index === 1 && selectedServer ? (
                    <Typography variant="caption">{selectedServer.name}</Typography>
                  ) : null
                }
              >
                {label}
              </StepLabel>
              <StepContent>
                {index === activeStep && renderStepContent()}
              </StepContent>
            </Step>
          ))}
        </Stepper>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={isPublishing}>
          Cancelar
        </Button>
        
        {activeStep > 0 && (
          <Button onClick={handleBack} disabled={isPublishing}>
            Atrás
          </Button>
        )}

        {activeStep < STEPS.length - 1 ? (
          <Button
            variant="contained"
            onClick={() => setActiveStep(activeStep + 1)}
            disabled={
              (activeStep === 0 && !selectedCameraId) ||
              (activeStep === 1 && !selectedServerId)
            }
          >
            Siguiente
          </Button>
        ) : (
          <Button
            variant="contained"
            onClick={handlePublish}
            disabled={isPublishing || !selectedCameraId || !selectedServerId}
            startIcon={isPublishing ? <CircularProgress size={20} /> : <PlayIcon />}
          >
            {isPublishing ? 'Publicando...' : 'Iniciar Publicación'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};