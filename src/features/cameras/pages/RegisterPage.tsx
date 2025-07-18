/**
 * 📝 Register Page - Universal Camera Viewer
 * Página de registro y gestión de cámaras
 * Optimizada con memo, callbacks memoizados y renderizado eficiente
 */

import React, { useState, useEffect, useCallback, useMemo, memo } from "react";
import {
  Box,
  Typography,
  Button,
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Skeleton,
} from "@mui/material";
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Download as ExportIcon,
  Upload as ImportIcon,
  Settings as SettingsIcon,
  CheckCircle as ConnectedIcon,
  Cancel as DisconnectedIcon,
} from "@mui/icons-material";
import { useCameraStoreV2 } from "../../../stores/cameraStore.v2";
import { useNotificationStore } from "../../../stores/notificationStore";
import { colorTokens } from "../../../design-system/tokens";

// Componente de fila de tabla memoizado para mejor rendimiento
interface CameraRowProps {
  camera: any;
  onEdit: (cameraId: string) => void;
  onDelete: (cameraId: string) => void;
  onSettings: (cameraId: string) => void;
}

const CameraRow = memo<CameraRowProps>(({ camera, onEdit, onDelete, onSettings }) => {
  return (
    <TableRow hover>
      <TableCell>
        {camera.is_connected ? (
          <Tooltip title="Conectada">
            <ConnectedIcon
              sx={{ color: colorTokens.status.connected }}
            />
          </Tooltip>
        ) : (
          <Tooltip title="Desconectada">
            <DisconnectedIcon
              sx={{ color: colorTokens.status.disconnected }}
            />
          </Tooltip>
        )}
      </TableCell>
      <TableCell>
        <Typography variant="body2" fontWeight={500}>
          {camera.display_name || `Cámara ${camera.camera_id}`}
        </Typography>
      </TableCell>
      <TableCell>
        <Typography variant="body2" fontFamily="monospace">
          {camera.ip_address}
        </Typography>
      </TableCell>
      <TableCell>{camera.brand || "—"}</TableCell>
      <TableCell>{camera.model || "—"}</TableCell>
      <TableCell>
        <Chip
          label={camera.protocol?.toUpperCase() || "AUTO"}
          size="small"
          variant="outlined"
        />
      </TableCell>
      <TableCell align="right">
        <Tooltip title="Configurar">
          <IconButton
            size="small"
            onClick={() => onSettings(camera.camera_id)}
          >
            <SettingsIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Editar">
          <IconButton
            size="small"
            onClick={() => onEdit(camera.camera_id)}
          >
            <EditIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Eliminar">
          <IconButton
            size="small"
            onClick={() => onDelete(camera.camera_id)}
            disabled={camera.is_connected}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </TableCell>
    </TableRow>
  );
});

CameraRow.displayName = 'CameraRow';

// Componente de skeleton para carga
const TableSkeleton = memo(() => (
  <>
    {[1, 2, 3, 4, 5].map((index) => (
      <TableRow key={index}>
        <TableCell><Skeleton variant="circular" width={24} height={24} /></TableCell>
        <TableCell><Skeleton variant="text" width="80%" /></TableCell>
        <TableCell><Skeleton variant="text" width="60%" /></TableCell>
        <TableCell><Skeleton variant="text" width="50%" /></TableCell>
        <TableCell><Skeleton variant="text" width="50%" /></TableCell>
        <TableCell><Skeleton variant="rectangular" width={60} height={20} /></TableCell>
        <TableCell align="right">
          <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
            <Skeleton variant="circular" width={32} height={32} />
            <Skeleton variant="circular" width={32} height={32} />
            <Skeleton variant="circular" width={32} height={32} />
          </Box>
        </TableCell>
      </TableRow>
    ))}
  </>
));

TableSkeleton.displayName = 'TableSkeleton';

const RegisterPage = memo(() => {
  const {
    cameras,
    isLoading,
    loadCameras,
    deleteCamera,
    getCameraStats,
  } = useCameraStoreV2();
  const { addNotification } = useNotificationStore();
  const [selectedCamera, setSelectedCamera] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [addDialogOpen, setAddDialogOpen] = useState(false);

  // Cargar todas las cámaras
  useEffect(() => {
    loadCameras();
  }, [loadCameras]);

  // Obtener todas las cámaras con memoización
  const allCameras = useMemo(() => Array.from(cameras.values()), [cameras]);
  const stats = useMemo(() => getCameraStats(), [getCameraStats, cameras]);

  // Handlers optimizados con useCallback
  const handleRefresh = useCallback(async () => {
    await loadCameras();
    addNotification({
      title: "Actualización",
      message: "Lista de cámaras actualizada",
      type: "info",
    });
  }, [loadCameras, addNotification]);

  const handleAddCamera = useCallback(() => {
    setAddDialogOpen(true);
  }, []);

  const handleEditCamera = useCallback((cameraId: string) => {
    addNotification({
      title: "En desarrollo",
      message: "Función de edición en desarrollo",
      type: "info",
    });
  }, [addNotification]);

  const handleSettingsCamera = useCallback((cameraId: string) => {
    addNotification({
      title: "En desarrollo",
      message: "Función de configuración en desarrollo",
      type: "info",
    });
  }, [addNotification]);

  const handleDeleteCamera = useCallback(async () => {
    if (!selectedCamera) return;

    try {
      await deleteCamera(selectedCamera);
      addNotification({
        title: "Éxito",
        message: "Cámara eliminada exitosamente",
        type: "success",
      });
      setDeleteDialogOpen(false);
      setSelectedCamera(null);
    } catch (error) {
      addNotification({
        title: "Error",
        message: "Error al eliminar la cámara",
        type: "error",
      });
    }
  }, [selectedCamera, deleteCamera, addNotification]);

  const handleExport = useCallback(() => {
    addNotification({
      title: "En desarrollo",
      message: "Función de exportación en desarrollo",
      type: "info",
    });
  }, [addNotification]);

  const handleImport = useCallback(() => {
    addNotification({
      title: "En desarrollo",
      message: "Función de importación en desarrollo",
      type: "info",
    });
  }, [addNotification]);

  const openDeleteDialog = useCallback((cameraId: string) => {
    setSelectedCamera(cameraId);
    setDeleteDialogOpen(true);
  }, []);

  const closeDeleteDialog = useCallback(() => {
    setDeleteDialogOpen(false);
    setSelectedCamera(null);
  }, []);

  const closeAddDialog = useCallback(() => {
    setAddDialogOpen(false);
  }, []);

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        width: "100%",
        gap: 2,
        p: 2,
      }}
    >
      {/* Header */}
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Registro de Cámaras
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Gestiona todas las cámaras del sistema. Total: {stats.total} | 
          Conectadas: {stats.connected} | Desconectadas: {stats.total - stats.connected}
        </Typography>
      </Box>

      {/* Toolbar */}
      <Paper
        elevation={0}
        sx={{
          p: 2,
          display: "flex",
          alignItems: "center",
          gap: 2,
          backgroundColor: (theme) =>
            theme.palette.mode === "dark"
              ? colorTokens.background.darkPaper
              : colorTokens.background.paper,
        }}
      >
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddCamera}
          sx={{ textTransform: "none" }}
        >
          Agregar Cámara
        </Button>

        <Box sx={{ flexGrow: 1 }} />

        <Tooltip title="Importar configuración">
          <IconButton onClick={handleImport}>
            <ImportIcon />
          </IconButton>
        </Tooltip>

        <Tooltip title="Exportar configuración">
          <IconButton onClick={handleExport}>
            <ExportIcon />
          </IconButton>
        </Tooltip>

        <Tooltip title="Actualizar lista">
          <IconButton onClick={handleRefresh} disabled={isLoading}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Paper>

      {/* Tabla de cámaras */}
      <TableContainer
        component={Paper}
        sx={{
          flex: 1,
          overflow: "auto",
          backgroundColor: (theme) =>
            theme.palette.mode === "dark"
              ? colorTokens.background.darkPaper
              : colorTokens.background.paper,
          // Optimización: usar will-change para preparar animaciones
          willChange: 'scroll-position',
        }}
      >
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell>Estado</TableCell>
              <TableCell>Nombre</TableCell>
              <TableCell>Dirección IP</TableCell>
              <TableCell>Marca</TableCell>
              <TableCell>Modelo</TableCell>
              <TableCell>Protocolo</TableCell>
              <TableCell align="right">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableSkeleton />
            ) : (
              allCameras.map((camera) => (
                <CameraRow
                  key={camera.camera_id}
                  camera={camera}
                  onEdit={handleEditCamera}
                  onDelete={openDeleteDialog}
                  onSettings={handleSettingsCamera}
                />
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialog de confirmación de eliminación */}
      <Dialog
        open={deleteDialogOpen}
        onClose={closeDeleteDialog}
      >
        <DialogTitle>Confirmar eliminación</DialogTitle>
        <DialogContent>
          <Typography>
            ¿Está seguro de que desea eliminar esta cámara? Esta acción no se
            puede deshacer.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDeleteDialog}>Cancelar</Button>
          <Button
            onClick={handleDeleteCamera}
            color="error"
            variant="contained"
          >
            Eliminar
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog para agregar cámara (placeholder) */}
      <Dialog
        open={addDialogOpen}
        onClose={closeAddDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Agregar Nueva Cámara</DialogTitle>
        <DialogContent>
          <Typography color="text.secondary">
            Formulario de agregar cámara en desarrollo...
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeAddDialog}>Cerrar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
});

// Añadir displayName para debugging
RegisterPage.displayName = 'RegisterPage';

export default RegisterPage;