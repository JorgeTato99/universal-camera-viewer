/**
 * 📝 Register Page - Universal Camera Viewer
 * Página de registro y gestión de cámaras
 */

import React, { useState, useEffect } from "react";
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

const RegisterPage: React.FC = () => {
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

  // Obtener todas las cámaras (conectadas y desconectadas)
  const allCameras = Array.from(cameras.values());
  const stats = getCameraStats();

  const handleRefresh = async () => {
    await loadCameras();
    addNotification({
      message: "Lista de cámaras actualizada",
      type: "info",
    });
  };

  const handleAddCamera = () => {
    setAddDialogOpen(true);
  };

  const handleEditCamera = (cameraId: string) => {
    addNotification({
      message: "Función de edición en desarrollo",
      type: "info",
    });
  };

  const handleDeleteCamera = async () => {
    if (!selectedCamera) return;

    try {
      await deleteCamera(selectedCamera);
      addNotification({
        message: "Cámara eliminada exitosamente",
        type: "success",
      });
      setDeleteDialogOpen(false);
      setSelectedCamera(null);
    } catch (error) {
      addNotification({
        message: "Error al eliminar la cámara",
        type: "error",
      });
    }
  };

  const handleExport = () => {
    addNotification({
      message: "Función de exportación en desarrollo",
      type: "info",
    });
  };

  const handleImport = () => {
    addNotification({
      message: "Función de importación en desarrollo",
      type: "info",
    });
  };

  const openDeleteDialog = (cameraId: string) => {
    setSelectedCamera(cameraId);
    setDeleteDialogOpen(true);
  };

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
          Conectadas: {stats.connected} | Desconectadas: {stats.disconnected}
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
          <IconButton onClick={handleRefresh}>
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
            {allCameras.map((camera) => (
              <TableRow key={camera.camera_id} hover>
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
                      onClick={() => handleEditCamera(camera.camera_id)}
                    >
                      <SettingsIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Editar">
                    <IconButton
                      size="small"
                      onClick={() => handleEditCamera(camera.camera_id)}
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Eliminar">
                    <IconButton
                      size="small"
                      onClick={() => openDeleteDialog(camera.camera_id)}
                      disabled={camera.is_connected}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialog de confirmación de eliminación */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Confirmar eliminación</DialogTitle>
        <DialogContent>
          <Typography>
            ¿Está seguro de que desea eliminar esta cámara? Esta acción no se
            puede deshacer.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancelar</Button>
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
        onClose={() => setAddDialogOpen(false)}
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
          <Button onClick={() => setAddDialogOpen(false)}>Cerrar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RegisterPage;