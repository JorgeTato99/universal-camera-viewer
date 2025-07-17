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
  useTheme,
  alpha,
} from '@mui/material';
import {
  KeyboardArrowDown as ExpandIcon,
  KeyboardArrowUp as CollapseIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  ContentCopy as CopyIcon,
  CheckCircle as TestIcon,
  Circle as StatusIcon,
  VpnKey as CredentialsIcon,
  Router as ProtocolIcon,
  Timeline as StatsIcon,
} from '@mui/icons-material';
import { CameraResponse, ConnectionStatus } from '../../../../types/camera.types.v2';
import { useCameraStoreV2 } from '../../../../stores/cameraStore.v2';

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
            <Box>
              <Typography variant="caption" color="text.secondary">
                Última conexión
              </Typography>
              <Typography variant="body2">
                {camera.last_connection_at ? new Date(camera.last_connection_at).toLocaleString() : 'Nunca'}
              </Typography>
            </Box>
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
          <Stack direction="row" spacing={3}>
            <Box>
              <Typography variant="h6" color="primary">
                {camera.total_connections || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Conexiones totales
              </Typography>
            </Box>
            <Box>
              <Typography variant="h6" color="success.main">
                {camera.successful_connections || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Exitosas
              </Typography>
            </Box>
            <Box>
              <Typography variant="h6" color="error.main">
                {camera.failed_connections || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Fallidas
              </Typography>
            </Box>
            <Box>
              <Typography variant="h6">
                {camera.success_rate ? `${camera.success_rate.toFixed(1)}%` : '0%'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Tasa de éxito
              </Typography>
            </Box>
          </Stack>
        </Box>
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
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell padding="checkbox">
              <Checkbox
                indeterminate={selectedCameras.size > 0 && selectedCameras.size < cameras.length}
                checked={cameras.length > 0 && selectedCameras.size === cameras.length}
                onChange={(e) => onSelectAll(e.target.checked)}
              />
            </TableCell>
            <TableCell />
            <TableCell>Nombre</TableCell>
            <TableCell>Dirección IP</TableCell>
            <TableCell>Marca / Modelo</TableCell>
            <TableCell>Puerto Principal</TableCell>
            <TableCell>Estado</TableCell>
            <TableCell align="center">Acciones</TableCell>
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
                  >
                    {expandedRows.has(camera.camera_id) ? <CollapseIcon /> : <ExpandIcon />}
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
                  <Chip
                    icon={<StatusIcon sx={{ fontSize: 12 }} />}
                    label={camera.status}
                    size="small"
                    sx={{
                      color: getStatusColor(camera.status),
                      borderColor: getStatusColor(camera.status),
                    }}
                    variant="outlined"
                  />
                </TableCell>
                <TableCell align="center">
                  <Stack direction="row" spacing={0.5} justifyContent="center">
                    <Tooltip title="Clonar configuración">
                      <IconButton size="small" onClick={() => handleClone(camera)}>
                        <CopyIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Eliminar">
                      <IconButton 
                        size="small" 
                        onClick={() => handleDelete(camera.camera_id)}
                        disabled={camera.is_connected}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Stack>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={8}>
                  <Collapse in={expandedRows.has(camera.camera_id)} timeout="auto" unmountOnExit>
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