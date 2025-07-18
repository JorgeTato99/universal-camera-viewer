/**
 * 🎯 Camera Data Table Component
 * Tabla de datos completa para gestión CRUD de cámaras
 */

import React, { useState } from 'react';
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Checkbox,
  IconButton,
  Collapse,
  Typography,
  Chip,
  Button,
  TextField,
  Tooltip,
  Stack,
  Divider,
  Switch,
  useTheme,
  alpha,
} from '@mui/material';
import {
  KeyboardArrowDown as ExpandIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  ContentCopy as CopyIcon,
  CheckCircle as TestIcon,
  VpnKey as CredentialsIcon,
  Router as ProtocolIcon,
  Timeline as StatsIcon,
  ControlCamera as PtzIcon,
  VolumeUp as AudioIcon,
  RemoveRedEye as IrIcon,
  Sensors as MotionIcon,
  AspectRatio as ResolutionIcon,
  Code as CodecIcon,
  Link as LinkIcon,
  PlayCircle as PlayIcon,
  CheckCircle,
} from '@mui/icons-material';
import { CameraResponse, ConnectionStatus } from '../../../../types/camera.types.v2';
import { useCameraStoreV2 } from '../../../../stores/cameraStore.v2';
import { notificationStore } from '../../../../stores/notificationStore';

interface CameraDataTableProps {
  cameras: CameraResponse[];
  selectedCameras: Set<string>;
  onSelectCamera: (cameraId: string, selected: boolean) => void;
  onSelectAll: (selected: boolean) => void;
}

interface ExpandedRowProps {
  camera: CameraResponse;
  onUpdate: (updates: Partial<CameraResponse>) => void;
}

const ExpandedRow: React.FC<ExpandedRowProps> = ({ camera, onUpdate }) => {
  const theme = useTheme();
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    location: camera.location || '',
    description: camera.description || '',
    username: camera.credentials?.username || '',
    rtsp_port: camera.protocols?.find(p => p?.protocol_type === 'rtsp')?.port || 554,
    onvif_port: camera.protocols?.find(p => p?.protocol_type === 'onvif')?.port || 80,
    http_port: camera.protocols?.find(p => p?.protocol_type === 'http')?.port || 80,
  });

  const handleSave = () => {
    onUpdate({
      location: editData.location,
      description: editData.description,
    });
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditData({
      location: camera.location || '',
      description: camera.description || '',
      username: camera.credentials?.username || '',
      rtsp_port: camera.protocols?.find(p => p?.protocol_type === 'rtsp')?.port || 554,
      onvif_port: camera.protocols?.find(p => p?.protocol_type === 'onvif')?.port || 80,
      http_port: camera.protocols?.find(p => p?.protocol_type === 'http')?.port || 80,
    });
    setIsEditing(false);
  };

  return (
    <Box sx={{ p: 3, bgcolor: alpha(theme.palette.background.default, 0.5) }}>
      <Stack spacing={3}>
        {/* Información básica */}
        <Box>
          <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
            Información General
          </Typography>
          <Stack direction="row" spacing={4} flexWrap="wrap">
            <Box>
              <Typography variant="caption" color="text.secondary">
                Dirección MAC
              </Typography>
              <Typography variant="body2" fontFamily="monospace">
                {camera.mac_address || 'No disponible'}
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Firmware
              </Typography>
              <Typography variant="body2">
                {camera.firmware_version || 'Desconocido'}
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Serial
              </Typography>
              <Typography variant="body2">
                {camera.serial_number || 'No disponible'}
              </Typography>
            </Box>
            {/* Comentado: last_connection_at no existe en CameraResponse
            <Box>
              <Typography variant="caption" color="text.secondary">
                Última conexión
              </Typography>
              <Typography variant="body2">
                {camera.last_connection_at ? new Date(camera.last_connection_at).toLocaleString() : 'Nunca'}
              </Typography>
            </Box>
            */}
          </Stack>
        </Box>

        <Divider />

        {/* Ubicación y descripción */}
        <Box>
          <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              Ubicación y Descripción
            </Typography>
            {!isEditing ? (
              <IconButton size="small" onClick={() => setIsEditing(true)}>
                <EditIcon fontSize="small" />
              </IconButton>
            ) : (
              <Stack direction="row" spacing={1}>
                <IconButton size="small" color="primary" onClick={handleSave}>
                  <SaveIcon fontSize="small" />
                </IconButton>
                <IconButton size="small" onClick={handleCancel}>
                  <CancelIcon fontSize="small" />
                </IconButton>
              </Stack>
            )}
          </Stack>
          
          <Stack spacing={2}>
            <TextField
              fullWidth
              label="Ubicación"
              value={editData.location}
              onChange={(e) => setEditData({ ...editData, location: e.target.value })}
              disabled={!isEditing}
              size="small"
              placeholder="Ej: Entrada principal, Oficina 2do piso"
            />
            <TextField
              fullWidth
              label="Descripción"
              value={editData.description}
              onChange={(e) => setEditData({ ...editData, description: e.target.value })}
              disabled={!isEditing}
              size="small"
              multiline
              rows={2}
              placeholder="Notas adicionales sobre la cámara"
            />
          </Stack>
        </Box>

        <Divider />

        {/* Credenciales y Protocolos */}
        <Stack direction="row" spacing={4}>
          <Box flex={1}>
            <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
              <CredentialsIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              Credenciales
            </Typography>
            <Stack spacing={1}>
              <Box>
                <Typography variant="caption" color="text.secondary">Usuario</Typography>
                <Typography variant="body2">{camera.credentials?.username || 'No configurado'}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">Tipo de autenticación</Typography>
                <Typography variant="body2">{camera.credentials?.auth_type || 'basic'}</Typography>
              </Box>
              <Button
                size="small"
                startIcon={<TestIcon />}
                variant="outlined"
                sx={{ mt: 1 }}
              >
                Probar conexión
              </Button>
            </Stack>
          </Box>

          <Box flex={1}>
            <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
              <ProtocolIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              Protocolos Configurados
            </Typography>
            <Stack spacing={1}>
              {camera.protocols?.map((protocol, index) => (
                <Box key={protocol.protocol_type || `protocol-${index}`} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip
                    label={protocol.protocol_type?.toUpperCase() || 'DESCONOCIDO'}
                    size="small"
                    color={protocol.is_enabled ? 'success' : 'default'}
                    variant={protocol.is_primary ? 'filled' : 'outlined'}
                  />
                  <Typography variant="body2" color="text.secondary">
                    Puerto: {protocol.port || '—'}
                  </Typography>
                </Box>
              )) || (
                <Typography variant="body2" color="text.secondary">
                  No hay protocolos configurados
                </Typography>
              )}
            </Stack>
          </Box>
        </Stack>

        <Divider />

        {/* Estadísticas */}
        <Box>
          <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
            <StatsIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
            Estadísticas de Conexión
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 2 }}>
            {/* Comentado: las propiedades total_connections, successful_connections, failed_connections y success_rate no existen en CameraResponse
            <Box>
              <Typography variant="h6" color="primary">
                {camera.statistics?.total_connections || camera.total_connections || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Conexiones totales
              </Typography>
            </Box>
            <Box>
              <Typography variant="h6" color="success.main">
                {camera.statistics?.successful_connections || camera.successful_connections || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Exitosas
              </Typography>
            </Box>
            <Box>
              <Typography variant="h6" color="error.main">
                {camera.statistics?.failed_connections || camera.failed_connections || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Fallidas
              </Typography>
            </Box>
            <Box>
              <Typography variant="h6">
                {(camera.statistics?.success_rate !== undefined && camera.statistics?.success_rate !== null) || 
                 (camera.success_rate !== undefined && camera.success_rate !== null) ? 
                  `${(camera.statistics?.success_rate ?? camera.success_rate).toFixed(1)}%` : '0%'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Tasa de éxito
              </Typography>
            </Box>
            */}
            {camera.statistics?.total_uptime_minutes !== undefined && (
              <Box>
                <Typography variant="h6" color="info.main">
                  {camera.statistics.total_uptime_minutes >= 60 
                    ? `${(camera.statistics.total_uptime_minutes / 60).toFixed(1)}h`
                    : `${camera.statistics.total_uptime_minutes}m`}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Tiempo activo
                </Typography>
              </Box>
            )}
            {camera.statistics?.average_fps !== undefined && camera.statistics.average_fps !== null && (
              <Box>
                <Typography variant="h6">
                  {camera.statistics.average_fps.toFixed(1)} fps
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  FPS promedio
                </Typography>
              </Box>
            )}
            {camera.statistics?.average_latency_ms !== undefined && camera.statistics.average_latency_ms !== null && (
              <Box>
                <Typography variant="h6">
                  {camera.statistics.average_latency_ms.toFixed(0)} ms
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Latencia promedio
                </Typography>
              </Box>
            )}
          </Box>
          
          {/* Información de errores si existe */}
          {camera.statistics?.last_error_at && (
            <Box sx={{ mt: 2, p: 1.5, bgcolor: alpha(theme.palette.error.main, 0.05), borderRadius: 1 }}>
              <Typography variant="caption" color="error.main" fontWeight={500}>
                Último error: {new Date(camera.statistics.last_error_at).toLocaleString()}
              </Typography>
              {camera.statistics.last_error_message && (
                <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 0.5 }}>
                  {camera.statistics.last_error_message}
                </Typography>
              )}
            </Box>
          )}
        </Box>

        <Divider />

        {/* Capacidades */}
        {camera.capabilities && (
          <Box>
            <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
              Capacidades de la Cámara
            </Typography>
            <Box 
              sx={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                gap: 2,
              }}
            >
              <Box 
                sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 1,
                  p: 1.5,
                  borderRadius: 1,
                  bgcolor: alpha(theme.palette.background.paper, 0.5),
                  border: 1,
                  borderColor: camera.capabilities.has_ptz 
                    ? alpha(theme.palette.success.main, 0.3)
                    : 'divider',
                }}
              >
                <PtzIcon 
                  sx={{ 
                    color: camera.capabilities.has_ptz 
                      ? 'success.main' 
                      : 'action.disabled' 
                  }} 
                />
                <Box>
                  <Typography variant="body2" fontWeight={500}>
                    PTZ
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {camera.capabilities.has_ptz ? 'Soportado' : 'No disponible'}
                  </Typography>
                </Box>
              </Box>

              <Box 
                sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 1,
                  p: 1.5,
                  borderRadius: 1,
                  bgcolor: alpha(theme.palette.background.paper, 0.5),
                  border: 1,
                  borderColor: camera.capabilities.has_audio 
                    ? alpha(theme.palette.success.main, 0.3)
                    : 'divider',
                }}
              >
                <AudioIcon 
                  sx={{ 
                    color: camera.capabilities.has_audio 
                      ? 'success.main' 
                      : 'action.disabled' 
                  }} 
                />
                <Box>
                  <Typography variant="body2" fontWeight={500}>
                    Audio
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {camera.capabilities.has_audio ? 'Soportado' : 'No disponible'}
                  </Typography>
                </Box>
              </Box>

              <Box 
                sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 1,
                  p: 1.5,
                  borderRadius: 1,
                  bgcolor: alpha(theme.palette.background.paper, 0.5),
                  border: 1,
                  borderColor: camera.capabilities.has_ir 
                    ? alpha(theme.palette.success.main, 0.3)
                    : 'divider',
                }}
              >
                <IrIcon 
                  sx={{ 
                    color: camera.capabilities.has_ir 
                      ? 'success.main' 
                      : 'action.disabled' 
                  }} 
                />
                <Box>
                  <Typography variant="body2" fontWeight={500}>
                    Visión IR
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {camera.capabilities.has_ir ? 'Soportado' : 'No disponible'}
                  </Typography>
                </Box>
              </Box>

              <Box 
                sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 1,
                  p: 1.5,
                  borderRadius: 1,
                  bgcolor: alpha(theme.palette.background.paper, 0.5),
                  border: 1,
                  borderColor: camera.capabilities.has_motion_detection 
                    ? alpha(theme.palette.success.main, 0.3)
                    : 'divider',
                }}
              >
                <MotionIcon 
                  sx={{ 
                    color: camera.capabilities.has_motion_detection 
                      ? 'success.main' 
                      : 'action.disabled' 
                  }} 
                />
                <Box>
                  <Typography variant="body2" fontWeight={500}>
                    Detección
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {camera.capabilities.has_motion_detection ? 'Movimiento' : 'No disponible'}
                  </Typography>
                </Box>
              </Box>
            </Box>

            {/* Resolución y codecs */}
            <Stack spacing={2} sx={{ mt: 2 }}>
              {camera.capabilities.max_resolution && (
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <ResolutionIcon fontSize="small" />
                    Resolución máxima
                  </Typography>
                  <Typography variant="body2" fontWeight={500}>
                    {camera.capabilities.max_resolution}
                  </Typography>
                </Box>
              )}

              {camera.capabilities.supported_codecs && camera.capabilities.supported_codecs.length > 0 && (
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <CodecIcon fontSize="small" />
                    Codecs soportados
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                    {camera.capabilities.supported_codecs.map((codec) => (
                      <Chip
                        key={codec}
                        label={codec}
                        size="small"
                        variant="outlined"
                        sx={{ height: 24 }}
                      />
                    ))}
                  </Box>
                </Box>
              )}
            </Stack>
          </Box>
        )}

        <Divider />

        {/* Endpoints Configurados */}
        {camera.endpoints && camera.endpoints.length > 0 && (
          <Box>
            <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
              <LinkIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              Endpoints Configurados
            </Typography>
            <Stack spacing={2}>
              {camera.endpoints
                .sort((a, b) => {
                  // Primero los verificados, luego por prioridad
                  if (a.is_verified !== b.is_verified) {
                    return a.is_verified ? -1 : 1;
                  }
                  return (b.priority || 0) - (a.priority || 0);
                })
                .map((endpoint, index) => (
                  <Paper
                    key={`${endpoint.type}-${index}`}
                    variant="outlined"
                    sx={{
                      p: 2,
                      borderColor: endpoint.is_verified 
                        ? alpha(theme.palette.success.main, 0.3)
                        : 'divider',
                      transition: 'all 0.2s',
                      '&:hover': {
                        borderColor: endpoint.is_verified ? 'success.main' : 'primary.main',
                        bgcolor: alpha(theme.palette.primary.main, 0.02),
                      },
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                      <Box sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <Chip
                            label={endpoint.type?.toUpperCase().replace('_', ' ') || 'UNKNOWN'}
                            size="small"
                            color={endpoint.is_verified ? 'success' : 'default'}
                            variant={endpoint.is_verified ? 'filled' : 'outlined'}
                          />
                          {endpoint.is_verified && (
                            <Chip
                              icon={<CheckCircle sx={{ fontSize: 16 }} />}
                              label="Verificado"
                              size="small"
                              color="success"
                              variant="outlined"
                              sx={{ height: 20 }}
                            />
                          )}
                          {endpoint.response_time_ms && (
                            <Typography 
                              variant="caption" 
                              sx={{ 
                                color: endpoint.response_time_ms < 100 
                                  ? 'success.main' 
                                  : endpoint.response_time_ms < 500 
                                    ? 'warning.main' 
                                    : 'error.main',
                                fontWeight: 500,
                              }}
                            >
                              {endpoint.response_time_ms}ms
                            </Typography>
                          )}
                          {endpoint.priority > 0 && (
                            <Chip
                              label={`Prioridad ${endpoint.priority}`}
                              size="small"
                              variant="outlined"
                              sx={{ height: 20 }}
                            />
                          )}
                        </Box>
                        
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            fontFamily: 'monospace',
                            wordBreak: 'break-all',
                            color: 'text.primary',
                          }}
                        >
                          {endpoint.url}
                        </Typography>
                        
                        {endpoint.last_verified && (
                          <Typography 
                            variant="caption" 
                            color="text.secondary"
                            sx={{ display: 'block', mt: 0.5 }}
                          >
                            Última verificación: {new Date(endpoint.last_verified).toLocaleString()}
                          </Typography>
                        )}
                      </Box>
                      
                      <Stack direction="row" spacing={1} sx={{ ml: 2 }}>
                        <Tooltip title="Copiar URL">
                          <IconButton
                            size="small"
                            onClick={() => {
                              navigator.clipboard.writeText(endpoint.url);
                              notificationStore.addNotification({
                                type: 'success',
                                title: 'Copiado',
                                message: 'URL copiada al portapapeles',
                              });
                            }}
                          >
                            <CopyIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={endpoint.is_verified ? "Volver a verificar" : "Verificar endpoint"}>
                          <IconButton
                            size="small"
                            color={endpoint.is_verified ? "default" : "primary"}
                            onClick={() => {
                              // TODO: Implementar verificación de endpoint
                              console.log('Verify endpoint:', endpoint);
                            }}
                          >
                            <TestIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    </Box>
                  </Paper>
              ))}
            </Stack>
          </Box>
        )}

        <Divider />

        {/* Perfiles de Stream */}
        {camera.stream_profiles && camera.stream_profiles.length > 0 && (
          <Box>
            <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
              <PlayIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
              Perfiles de Stream
            </Typography>
            <Box 
              sx={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: 2,
              }}
            >
              {camera.stream_profiles.map((profile, index) => (
                <Paper
                  key={`${profile.profile_name || 'profile'}-${index}`}
                  variant="outlined"
                  sx={{
                    p: 2,
                    borderColor: profile.is_default 
                      ? alpha(theme.palette.primary.main, 0.3)
                      : 'divider',
                    position: 'relative',
                    overflow: 'hidden',
                  }}
                >
                  {profile.is_default && (
                    <Chip
                      label="Por defecto"
                      size="small"
                      color="primary"
                      sx={{
                        position: 'absolute',
                        top: 8,
                        right: 8,
                        height: 20,
                      }}
                    />
                  )}
                  
                  <Stack spacing={1.5}>
                    <Box>
                      <Typography variant="body2" fontWeight={600}>
                        {profile.profile_name || 'Sin nombre'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Tipo: {profile.stream_type?.toUpperCase() || 'MAIN'}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Resolución
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {profile.resolution || 'N/A'}
                        </Typography>
                      </Box>
                      
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          FPS
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {profile.fps || 'N/A'}
                        </Typography>
                      </Box>
                      
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Bitrate
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {profile.bitrate ? `${profile.bitrate} kbps` : 'N/A'}
                        </Typography>
                      </Box>
                      
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Codec
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {profile.codec || 'N/A'}
                        </Typography>
                      </Box>
                    </Box>
                    
                    {(profile.channel !== undefined || profile.subtype !== undefined) && (
                      <Box sx={{ pt: 1, borderTop: 1, borderColor: 'divider' }}>
                        <Typography variant="caption" color="text.secondary">
                          Canal: {profile.channel || 1} | Subtipo: {profile.subtype || 0}
                        </Typography>
                      </Box>
                    )}
                  </Stack>
                </Paper>
              ))}
            </Box>
          </Box>
        )}
      </Stack>
    </Box>
  );
};

export const CameraDataTable: React.FC<CameraDataTableProps> = ({
  cameras,
  selectedCameras,
  onSelectCamera,
  onSelectAll,
}) => {
  const theme = useTheme();
  const { updateCamera, deleteCamera, connectCamera, disconnectCamera } = useCameraStoreV2();
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const toggleRowExpansion = (cameraId: string) => {
    setExpandedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(cameraId)) {
        newSet.delete(cameraId);
      } else {
        newSet.add(cameraId);
      }
      return newSet;
    });
  };

  const getStatusColor = (status: ConnectionStatus) => {
    switch (status) {
      case ConnectionStatus.CONNECTED:
        return theme.palette.success.main;
      case ConnectionStatus.CONNECTING:
        return theme.palette.warning.main;
      case ConnectionStatus.ERROR:
        return theme.palette.error.main;
      default:
        return theme.palette.grey[500];
    }
  };

  const handleDelete = async (cameraId: string) => {
    if (window.confirm('¿Está seguro de eliminar esta cámara?')) {
      await deleteCamera(cameraId);
    }
  };

  const handleClone = (camera: CameraResponse) => {
    // TODO: Implementar clonación
    console.log('Clone camera:', camera);
  };

  return (
    <TableContainer 
      component={Paper}
      sx={{
        boxShadow: theme.shadows[1],
        borderRadius: 2,
        overflow: 'hidden',
      }}
    >
      <Table>
        <TableHead>
          <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.02) }}>
            <TableCell padding="checkbox">
              <Checkbox
                indeterminate={selectedCameras.size > 0 && selectedCameras.size < cameras.length}
                checked={cameras.length > 0 && selectedCameras.size === cameras.length}
                onChange={(e) => onSelectAll(e.target.checked)}
              />
            </TableCell>
            <TableCell sx={{ width: 50 }} />
            <TableCell sx={{ fontWeight: 600 }}>Nombre</TableCell>
            <TableCell sx={{ fontWeight: 600 }}>Dirección IP</TableCell>
            <TableCell sx={{ fontWeight: 600 }}>Marca / Modelo</TableCell>
            <TableCell sx={{ fontWeight: 600, width: 120 }}>Puerto</TableCell>
            <TableCell sx={{ fontWeight: 600, width: 140 }}>Estado</TableCell>
            <TableCell sx={{ fontWeight: 600, width: 80 }}>Activa</TableCell>
            <TableCell align="center" sx={{ fontWeight: 600, width: 100 }}>Acciones</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {cameras.map((camera) => (
            <React.Fragment key={camera.camera_id}>
              <TableRow hover>
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selectedCameras.has(camera.camera_id)}
                    onChange={(e) => onSelectCamera(camera.camera_id, e.target.checked)}
                  />
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => toggleRowExpansion(camera.camera_id)}
                    sx={{
                      transition: 'transform 0.2s',
                      transform: expandedRows.has(camera.camera_id) ? 'rotate(180deg)' : 'rotate(0deg)',
                    }}
                  >
                    <ExpandIcon />
                  </IconButton>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" fontWeight={500}>
                    {camera.display_name}
                  </Typography>
                  {camera.location && (
                    <Typography variant="caption" color="text.secondary">
                      {camera.location}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  <Typography variant="body2" fontFamily="monospace">
                    {camera.ip_address}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {camera.brand}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {camera.model}
                  </Typography>
                </TableCell>
                <TableCell>
                  {camera.protocols?.find(p => p?.is_primary)?.port || 
                   camera.protocols?.[0]?.port || 
                   '—'}
                </TableCell>
                <TableCell>
                  <Stack spacing={0.5}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box
                        sx={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          bgcolor: getStatusColor(camera.status),
                          animation: camera.status === ConnectionStatus.CONNECTING 
                            ? 'pulse 1.5s infinite' 
                            : 'none',
                          '@keyframes pulse': {
                            '0%': { opacity: 1 },
                            '50%': { opacity: 0.4 },
                            '100%': { opacity: 1 },
                          },
                        }}
                      />
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          color: getStatusColor(camera.status),
                          fontWeight: 500,
                        }}
                      >
                        {camera.status === ConnectionStatus.CONNECTED && 'Conectada'}
                        {camera.status === ConnectionStatus.CONNECTING && 'Conectando'}
                        {camera.status === ConnectionStatus.DISCONNECTED && 'Desconectada'}
                        {camera.status === ConnectionStatus.ERROR && 'Error'}
                      </Typography>
                    </Box>
                    {camera.is_connected && camera.is_streaming && (
                      <Typography 
                        variant="caption" 
                        sx={{ 
                          color: theme.palette.info.main,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 0.5,
                          ml: 2,
                        }}
                      >
                        <Box
                          component="span"
                          sx={{
                            width: 6,
                            height: 6,
                            borderRadius: '50%',
                            bgcolor: theme.palette.info.main,
                            display: 'inline-block',
                          }}
                        />
                        Transmitiendo
                      </Typography>
                    )}
                  </Stack>
                </TableCell>
                <TableCell>
                  <Tooltip title={camera.is_active ? "Cámara activa" : "Cámara inactiva"}>
                    <Switch
                      size="small"
                      checked={camera.is_active}
                      onChange={async (e) => {
                        await updateCamera(camera.camera_id, { is_active: e.target.checked });
                      }}
                      sx={{
                        '& .MuiSwitch-track': {
                          bgcolor: camera.is_active 
                            ? alpha(theme.palette.success.main, 0.5) 
                            : alpha(theme.palette.action.disabled, 0.3),
                        },
                      }}
                    />
                  </Tooltip>
                </TableCell>
                <TableCell align="center">
                  <Stack direction="row" spacing={0.5} justifyContent="center">
                    <Tooltip title="Clonar configuración">
                      <IconButton 
                        size="small" 
                        onClick={() => handleClone(camera)}
                        sx={{
                          '&:hover': {
                            bgcolor: alpha(theme.palette.primary.main, 0.1),
                            color: 'primary.main',
                          },
                        }}
                      >
                        <CopyIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={camera.is_connected ? "Desconectar primero" : "Eliminar"}>
                      <span>
                        <IconButton 
                          size="small" 
                          onClick={() => handleDelete(camera.camera_id)}
                          disabled={camera.is_connected}
                          sx={{
                            '&:hover:not(:disabled)': {
                              bgcolor: alpha(theme.palette.error.main, 0.1),
                              color: 'error.main',
                            },
                          }}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>
                  </Stack>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell 
                  style={{ paddingBottom: 0, paddingTop: 0 }} 
                  colSpan={9}
                  sx={{
                    bgcolor: expandedRows.has(camera.camera_id) 
                      ? alpha(theme.palette.background.default, 0.5) 
                      : 'transparent',
                    transition: 'background-color 0.2s',
                  }}
                >
                  <Collapse 
                    in={expandedRows.has(camera.camera_id)} 
                    timeout={{ enter: 300, exit: 200 }} 
                    unmountOnExit
                  >
                    <ExpandedRow 
                      camera={camera} 
                      onUpdate={(updates) => updateCamera(camera.camera_id, updates)}
                    />
                  </Collapse>
                </TableCell>
              </TableRow>
            </React.Fragment>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};