/**
 * 🌐 MediaMTX Servers Page - Universal Camera Viewer
 * Página de gestión de servidores MediaMTX remotos
 */

import React, { useEffect, useState, useCallback, memo } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Button,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Checkbox,
  Alert,
  Chip,
  Fade,
  CircularProgress,
  Menu,
  MenuItem,
  Skeleton,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Link as LinkIcon,
  LinkOff as LinkOffIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { DataTable } from '../../../components/common/DataTable';
import { ConfirmationDialog } from '../../../components/common/ConfirmationDialog';
import { MediaMTXAuthDialog } from '../components/auth/MediaMTXAuthDialog';
import { usePublishingStore } from '../../../stores/publishingStore';
import { mediamtxServerService } from '../../../services/publishing/mediamtxServerService';
import { colorTokens } from '../../../design-system/tokens';
import type { MediaMTXServer, CreateServerDto, UpdateServerDto } from '../../../services/publishing/mediamtxServerService';

/**
 * Formulario de servidor (crear/editar)
 */
interface ServerFormData {
  name: string;
  api_url: string;
  rtmp_url: string;
  rtsp_url: string;
  auth_required: boolean;
  username?: string;
  password?: string;
}

/**
 * Diálogo de formulario de servidor
 */
const ServerFormDialog = memo<{
  open: boolean;
  server?: MediaMTXServer | null;
  onClose: () => void;
  onSave: (data: ServerFormData) => Promise<void>;
}>(({ open, server, onClose, onSave }) => {
  const [formData, setFormData] = useState<ServerFormData>({
    name: '',
    api_url: 'http://localhost:9997',
    rtmp_url: 'rtmp://localhost:1935',
    rtsp_url: 'rtsp://localhost:8554',
    auth_required: false,
    username: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof ServerFormData, string>>>({});

  // Cargar datos del servidor si está editando
  useEffect(() => {
    if (server) {
      setFormData({
        name: server.name,
        api_url: server.api_url,
        rtmp_url: server.rtmp_url,
        rtsp_url: server.rtsp_url,
        auth_required: server.auth_required,
        username: '', // No cargamos credenciales por seguridad
        password: '',
      });
    } else {
      // Reset para nuevo servidor
      setFormData({
        name: '',
        api_url: 'http://localhost:9997',
        rtmp_url: 'rtmp://localhost:1935',
        rtsp_url: 'rtsp://localhost:8554',
        auth_required: false,
        username: '',
        password: '',
      });
    }
    setErrors({});
  }, [server]);

  // Validar formulario
  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof ServerFormData, string>> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'El nombre es obligatorio';
    }

    if (!formData.api_url.trim()) {
      newErrors.api_url = 'La URL de API es obligatoria';
    } else if (!formData.api_url.match(/^https?:\/\/.+/)) {
      newErrors.api_url = 'Debe ser una URL válida (http:// o https://)';
    }

    if (!formData.rtmp_url.trim()) {
      newErrors.rtmp_url = 'La URL RTMP es obligatoria';
    } else if (!formData.rtmp_url.match(/^rtmp:\/\/.+/)) {
      newErrors.rtmp_url = 'Debe ser una URL RTMP válida';
    }

    if (!formData.rtsp_url.trim()) {
      newErrors.rtsp_url = 'La URL RTSP es obligatoria';
    } else if (!formData.rtsp_url.match(/^rtsp:\/\/.+/)) {
      newErrors.rtsp_url = 'Debe ser una URL RTSP válida';
    }

    if (formData.auth_required && !server) {
      // Solo validar credenciales en creación si auth está habilitado
      if (!formData.username?.trim()) {
        newErrors.username = 'El usuario es obligatorio si requiere autenticación';
      }
      if (!formData.password?.trim()) {
        newErrors.password = 'La contraseña es obligatoria si requiere autenticación';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Manejar envío
  const handleSubmit = async () => {
    if (!validateForm()) return;

    setLoading(true);
    try {
      await onSave(formData);
      onClose();
    } catch (error) {
      console.error('Error guardando servidor:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {server ? 'Editar Servidor MediaMTX' : 'Agregar Servidor MediaMTX'}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <TextField
            label="Nombre del servidor"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            error={!!errors.name}
            helperText={errors.name}
            fullWidth
            required
          />

          <TextField
            label="URL de API"
            value={formData.api_url}
            onChange={(e) => setFormData({ ...formData, api_url: e.target.value })}
            error={!!errors.api_url}
            helperText={errors.api_url || 'Ej: http://servidor.com:9997'}
            fullWidth
            required
          />

          <TextField
            label="URL RTMP"
            value={formData.rtmp_url}
            onChange={(e) => setFormData({ ...formData, rtmp_url: e.target.value })}
            error={!!errors.rtmp_url}
            helperText={errors.rtmp_url || 'Ej: rtmp://servidor.com:1935'}
            fullWidth
            required
          />

          <TextField
            label="URL RTSP"
            value={formData.rtsp_url}
            onChange={(e) => setFormData({ ...formData, rtsp_url: e.target.value })}
            error={!!errors.rtsp_url}
            helperText={errors.rtsp_url || 'Ej: rtsp://servidor.com:8554'}
            fullWidth
            required
          />

          <FormControlLabel
            control={
              <Checkbox
                checked={formData.auth_required}
                onChange={(e) => setFormData({ ...formData, auth_required: e.target.checked })}
              />
            }
            label="Requiere autenticación"
          />

          {formData.auth_required && !server && (
            <>
              <Alert severity="info">
                Las credenciales se usarán solo para la configuración inicial
              </Alert>
              <TextField
                label="Usuario"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                error={!!errors.username}
                helperText={errors.username}
                fullWidth
                autoComplete="username"
              />
              <TextField
                label="Contraseña"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                error={!!errors.password}
                helperText={errors.password}
                fullWidth
                autoComplete="new-password"
              />
            </>
          )}

          {server && formData.auth_required && (
            <Alert severity="info">
              Para cambiar las credenciales, use el botón "Autenticar" después de guardar
            </Alert>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancelar
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading}
          startIcon={loading && <CircularProgress size={16} />}
        >
          {server ? 'Guardar cambios' : 'Agregar servidor'}
        </Button>
      </DialogActions>
    </Dialog>
  );
});

ServerFormDialog.displayName = 'ServerFormDialog';

/**
 * Página de gestión de servidores MediaMTX
 */
const MediaMTXServersPage = memo(() => {
  const { remote, fetchRemoteServers } = usePublishingStore();
  const [formDialogOpen, setFormDialogOpen] = useState(false);
  const [authDialogOpen, setAuthDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedServer, setSelectedServer] = useState<MediaMTXServer | null>(null);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [testingConnection, setTestingConnection] = useState<number | null>(null);

  // Cargar servidores al montar
  useEffect(() => {
    fetchRemoteServers();
  }, [fetchRemoteServers]);

  // Crear servidor
  const handleCreateServer = useCallback(async (data: ServerFormData) => {
    try {
      const createDto: CreateServerDto = {
        name: data.name,
        api_url: data.api_url,
        rtmp_url: data.rtmp_url,
        rtsp_url: data.rtsp_url,
        auth_required: data.auth_required,
        username: data.username,
        password: data.password,
      };

      await mediamtxServerService.createServer(createDto);
      await fetchRemoteServers(); // Recargar lista
    } catch (error) {
      console.error('Error creando servidor:', error);
      throw error;
    }
  }, [fetchRemoteServers]);

  // Actualizar servidor
  const handleUpdateServer = useCallback(async (data: ServerFormData) => {
    if (!selectedServer) return;

    try {
      const updateDto: UpdateServerDto = {
        name: data.name,
        api_url: data.api_url,
        rtmp_url: data.rtmp_url,
        rtsp_url: data.rtsp_url,
        auth_required: data.auth_required,
      };

      await mediamtxServerService.updateServer(selectedServer.id, updateDto);
      await fetchRemoteServers(); // Recargar lista
    } catch (error) {
      console.error('Error actualizando servidor:', error);
      throw error;
    }
  }, [selectedServer, fetchRemoteServers]);

  // Eliminar servidor
  const handleDeleteServer = useCallback(async () => {
    if (!selectedServer) return;

    try {
      await mediamtxServerService.deleteServer(selectedServer.id);
      await fetchRemoteServers(); // Recargar lista
      setDeleteDialogOpen(false);
      setSelectedServer(null);
    } catch (error) {
      console.error('Error eliminando servidor:', error);
    }
  }, [selectedServer, fetchRemoteServers]);

  // Probar conexión
  const handleTestConnection = useCallback(async (server: MediaMTXServer) => {
    setTestingConnection(server.id);
    try {
      await mediamtxServerService.testConnection(server.id);
    } catch (error) {
      console.error('Error probando conexión:', error);
    } finally {
      setTestingConnection(null);
    }
  }, []);

  // Abrir menú de acciones
  const handleOpenMenu = (event: React.MouseEvent<HTMLElement>, server: MediaMTXServer) => {
    setMenuAnchor(event.currentTarget);
    setSelectedServer(server);
  };

  // Cerrar menú
  const handleCloseMenu = () => {
    setMenuAnchor(null);
  };

  // Columnas de la tabla
  const columns = [
    {
      field: 'name',
      headerName: 'Nombre',
      flex: 1,
      renderCell: (row: MediaMTXServer) => (
        <Box>
          <Typography variant="body2" fontWeight={500}>
            {row.name}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            ID: {row.id}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'api_url',
      headerName: 'URL del Servidor',
      flex: 1.5,
      renderCell: (row: MediaMTXServer) => (
        <Box>
          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
            {row.api_url}
          </Typography>
          <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
            <Chip label="RTMP" size="small" variant="outlined" />
            <Chip label="RTSP" size="small" variant="outlined" />
          </Box>
        </Box>
      ),
    },
    {
      field: 'status',
      headerName: 'Estado',
      width: 200,
      renderCell: (row: MediaMTXServer) => (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {row.is_active ? (
              <CheckIcon sx={{ fontSize: 20, color: colorTokens.status.connected }} />
            ) : (
              <WarningIcon sx={{ fontSize: 20, color: colorTokens.neutral[500] }} />
            )}
            <Typography variant="body2">
              {row.is_active ? 'Activo' : 'Inactivo'}
            </Typography>
          </Box>
          {row.is_authenticated ? (
            <Chip
              icon={<LinkIcon sx={{ fontSize: 14 }} />}
              label="Autenticado"
              size="small"
              color="success"
              variant="filled"
            />
          ) : (
            <Chip
              icon={<LinkOffIcon sx={{ fontSize: 14 }} />}
              label="Sin autenticar"
              size="small"
              color="default"
              variant="outlined"
            />
          )}
        </Box>
      ),
    },
    {
      field: 'last_health_check',
      headerName: 'Última verificación',
      width: 180,
      renderCell: (row: MediaMTXServer) => (
        <Typography variant="body2" color="text.secondary">
          {row.last_health_check
            ? new Date(row.last_health_check).toLocaleString('es-ES', {
                day: '2-digit',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit',
              })
            : 'Nunca'}
        </Typography>
      ),
    },
    {
      field: 'actions',
      headerName: 'Acciones',
      width: 300,
      sortable: false,
      renderCell: (row: MediaMTXServer) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          {!row.is_authenticated ? (
            <Button
              size="small"
              variant="contained"
              startIcon={<LinkIcon />}
              onClick={() => {
                setSelectedServer(row);
                setAuthDialogOpen(true);
              }}
            >
              Autenticar
            </Button>
          ) : (
            <Button
              size="small"
              variant="outlined"
              startIcon={<CheckIcon />}
              disabled
            >
              Autenticado
            </Button>
          )}
          <Tooltip title="Probar conexión">
            <IconButton
              size="small"
              onClick={() => handleTestConnection(row)}
              disabled={testingConnection === row.id}
            >
              {testingConnection === row.id ? (
                <CircularProgress size={20} />
              ) : (
                <SpeedIcon />
              )}
            </IconButton>
          </Tooltip>
          <IconButton
            size="small"
            onClick={(e) => handleOpenMenu(e, row)}
          >
            <MoreIcon />
          </IconButton>
        </Box>
      ),
    },
  ];

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Fade in timeout={300}>
        <Box>
          {/* Header */}
          <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h4" gutterBottom>
                Servidores MediaMTX
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Gestiona los servidores MediaMTX remotos para publicación de cámaras
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={() => fetchRemoteServers()}
                disabled={remote.isLoadingServers}
              >
                Actualizar
              </Button>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => {
                  setSelectedServer(null);
                  setFormDialogOpen(true);
                }}
              >
                Agregar Servidor
              </Button>
            </Box>
          </Box>

          {/* Tabla de servidores */}
          <Paper>
            {remote.isLoadingServers && remote.servers.length === 0 ? (
              <Box sx={{ p: 3 }}>
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} height={80} sx={{ mb: 2 }} />
                ))}
              </Box>
            ) : (
              <DataTable
                columns={columns}
                data={remote.servers}
                getRowId={(row: MediaMTXServer) => row.id.toString()}
                emptyMessage="No hay servidores configurados"
                emptyAction={
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => {
                      setSelectedServer(null);
                      setFormDialogOpen(true);
                    }}
                  >
                    Configurar primer servidor
                  </Button>
                }
              />
            )}
          </Paper>

          {/* Menú de acciones */}
          <Menu
            anchorEl={menuAnchor}
            open={Boolean(menuAnchor)}
            onClose={handleCloseMenu}
          >
            <MenuItem
              onClick={() => {
                handleCloseMenu();
                setFormDialogOpen(true);
              }}
            >
              <EditIcon sx={{ mr: 1, fontSize: 20 }} />
              Editar
            </MenuItem>
            <MenuItem
              onClick={() => {
                handleCloseMenu();
                setDeleteDialogOpen(true);
              }}
              sx={{ color: 'error.main' }}
            >
              <DeleteIcon sx={{ mr: 1, fontSize: 20 }} />
              Eliminar
            </MenuItem>
          </Menu>

          {/* Diálogo de formulario */}
          <ServerFormDialog
            open={formDialogOpen}
            server={selectedServer}
            onClose={() => {
              setFormDialogOpen(false);
              setSelectedServer(null);
            }}
            onSave={selectedServer ? handleUpdateServer : handleCreateServer}
          />

          {/* Diálogo de autenticación */}
          {selectedServer && (
            <MediaMTXAuthDialog
              open={authDialogOpen}
              server={selectedServer}
              onClose={() => {
                setAuthDialogOpen(false);
                setSelectedServer(null);
              }}
              onAuthSuccess={() => {
                setAuthDialogOpen(false);
                setSelectedServer(null);
                fetchRemoteServers();
              }}
            />
          )}

          {/* Diálogo de confirmación de eliminación */}
          <ConfirmationDialog
            open={deleteDialogOpen}
            title="Eliminar servidor"
            message={`¿Estás seguro de que deseas eliminar el servidor "${selectedServer?.name}"? Esta acción no se puede deshacer.`}
            severity="error"
            confirmText="Eliminar"
            onConfirm={handleDeleteServer}
            onCancel={() => {
              setDeleteDialogOpen(false);
              setSelectedServer(null);
            }}
          />
        </Box>
      </Fade>
    </Container>
  );
});

MediaMTXServersPage.displayName = 'MediaMTXServersPage';

export default MediaMTXServersPage;