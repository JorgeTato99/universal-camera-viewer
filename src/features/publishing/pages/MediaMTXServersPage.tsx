/**
 * ☁️ Remote MediaMTX Servers Page - Universal Camera Viewer
 * Página de gestión de servidores MediaMTX remotos
 *
 * @todo Funcionalidades pendientes:
 * - Implementar importación/exportación de configuraciones de servidor
 * - Agregar monitoreo de salud en tiempo real con gráficas
 * - Implementar gestión de permisos por servidor
 * - Agregar soporte para configuración avanzada de MediaMTX
 * - Implementar logs de servidor en tiempo real
 * - Agregar soporte para múltiples credenciales por servidor
 *
 * @note Esta página gestiona exclusivamente servidores remotos (90% caso de uso)
 */

import React, { useEffect, useState, useCallback, memo } from "react";
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
  CircularProgress,
  Menu,
  MenuItem,
  InputAdornment,
  Card,
  CardContent,
} from "@mui/material";
import Grid from "@mui/material/Grid";
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
  Api as ApiIcon,
  CloudQueue as CloudIcon,
  Lock as LockIcon,
  LockOpen as LockOpenIcon,
  Info as InfoIcon,
  Public as PublicIcon,
} from "@mui/icons-material";
import { DataTable } from "../../../components/common/DataTable";
import { ConfirmationDialog } from "../../../components/common/ConfirmationDialog";
import { ServerAuthDialog } from "../components/ServerAuthDialog";
import { usePublishingStore } from "../../../stores/publishingStore";
import { mediamtxServerService } from "../../../services/publishing/mediamtxServerService";
import { colorTokens } from "../../../design-system/tokens";
import { WelcomeWizard, useFirstTimeUser } from "../components/wizard";
import { SkeletonTable } from "../../../components/common/LoadingStates";
import { PageTransition } from "../../../components/common/PageTransition";
import { motion } from "framer-motion";
import type {
  MediaMTXServer,
  CreateServerDto,
  UpdateServerDto,
} from "../../../services/publishing/mediamtxServerService";

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
    name: "",
    api_url: "http://localhost:9997",
    rtmp_url: "rtmp://localhost:1935",
    rtsp_url: "rtsp://localhost:8554",
    auth_required: false,
    username: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<
    Partial<Record<keyof ServerFormData, string>>
  >({});

  // Cargar datos del servidor si está editando
  useEffect(() => {
    if (server) {
      setFormData({
        name: server.name || server.server_name || "",
        api_url: server.api_url,
        rtmp_url: server.rtmp_url,
        rtsp_url: server.rtsp_url,
        auth_required: server.auth_required ?? false,
        username: "", // No cargamos credenciales por seguridad
        password: "",
      });
    } else {
      // Reset para nuevo servidor
      setFormData({
        name: "",
        api_url: "http://localhost:9997",
        rtmp_url: "rtmp://localhost:1935",
        rtsp_url: "rtsp://localhost:8554",
        auth_required: false,
        username: "",
        password: "",
      });
    }
    setErrors({});
  }, [server]);

  // Validar formulario
  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof ServerFormData, string>> = {};

    if (!formData.name.trim()) {
      newErrors.name = "El nombre es obligatorio";
    }

    if (!formData.api_url.trim()) {
      newErrors.api_url = "La URL de API es obligatoria";
    } else if (!formData.api_url.match(/^https?:\/\/.+/)) {
      newErrors.api_url = "Debe ser una URL válida (http:// o https://)";
    }

    if (!formData.rtmp_url.trim()) {
      newErrors.rtmp_url = "La URL RTMP es obligatoria";
    } else if (!formData.rtmp_url.match(/^rtmp:\/\/.+/)) {
      newErrors.rtmp_url = "Debe ser una URL RTMP válida";
    }

    if (!formData.rtsp_url.trim()) {
      newErrors.rtsp_url = "La URL RTSP es obligatoria";
    } else if (!formData.rtsp_url.match(/^rtsp:\/\/.+/)) {
      newErrors.rtsp_url = "Debe ser una URL RTSP válida";
    }

    if (formData.auth_required && !server) {
      // Solo validar credenciales en creación si auth está habilitado
      if (!formData.username?.trim()) {
        newErrors.username =
          "El usuario es obligatorio si requiere autenticación";
      }
      if (!formData.password?.trim()) {
        newErrors.password =
          "La contraseña es obligatoria si requiere autenticación";
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
      console.error("Error guardando servidor:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      slotProps={{
        paper: {
          sx: {
            borderRadius: 2,
            boxShadow: 24,
          },
        },
      }}
    >
      <DialogTitle
        sx={{
          bgcolor: "primary.main",
          color: "primary.contrastText",
          display: "flex",
          alignItems: "center",
          gap: 1,
        }}
      >
        <CloudIcon />
        {server ? "Editar Servidor Remoto" : "Agregar Servidor MediaMTX Remoto"}
      </DialogTitle>
      <DialogContent sx={{ mt: 3 }}>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
          {/* Información básica */}
          <Box>
            <Typography
              variant="subtitle2"
              sx={{ mb: 2, fontWeight: 600, color: "text.secondary" }}
            >
              INFORMACIÓN BÁSICA
            </Typography>
            <TextField
              label="Nombre del servidor"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              error={!!errors.name}
              helperText={errors.name}
              fullWidth
              required
              placeholder="Mi servidor remoto"
              sx={{ mb: 2 }}
            />
          </Box>

          {/* URLs de conexión */}
          <Box>
            <Typography
              variant="subtitle2"
              sx={{ mb: 2, fontWeight: 600, color: "text.secondary" }}
            >
              URLS DE CONEXIÓN
            </Typography>
            <Grid container spacing={2}>
              <Grid size={12}>
                <TextField
                  label="URL de API"
                  value={formData.api_url}
                  onChange={(e) =>
                    setFormData({ ...formData, api_url: e.target.value })
                  }
                  error={!!errors.api_url}
                  helperText={errors.api_url || "Puerto por defecto: 9997"}
                  fullWidth
                  required
                  placeholder="http://servidor.com:9997"
                  slotProps={{
                    input: {
                      startAdornment: (
                        <InputAdornment position="start">
                          <ApiIcon sx={{ color: "action.active" }} />
                        </InputAdornment>
                      ),
                    },
                  }}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  label="URL RTMP"
                  value={formData.rtmp_url}
                  onChange={(e) =>
                    setFormData({ ...formData, rtmp_url: e.target.value })
                  }
                  error={!!errors.rtmp_url}
                  helperText={errors.rtmp_url || "Puerto por defecto: 1935"}
                  fullWidth
                  required
                  placeholder="rtmp://servidor.com:1935"
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  label="URL RTSP"
                  value={formData.rtsp_url}
                  onChange={(e) =>
                    setFormData({ ...formData, rtsp_url: e.target.value })
                  }
                  error={!!errors.rtsp_url}
                  helperText={errors.rtsp_url || "Puerto por defecto: 8554"}
                  fullWidth
                  required
                  placeholder="rtsp://servidor.com:8554"
                />
              </Grid>
            </Grid>
          </Box>

          {/* Configuración de seguridad */}
          <Box>
            <Typography
              variant="subtitle2"
              sx={{ mb: 2, fontWeight: 600, color: "text.secondary" }}
            >
              CONFIGURACIÓN DE SEGURIDAD
            </Typography>

            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.auth_required}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      auth_required: e.target.checked,
                    })
                  }
                  icon={<LockOpenIcon />}
                  checkedIcon={<LockIcon />}
                  sx={{
                    color: "action.active",
                    "&.Mui-checked": {
                      color: "warning.main",
                    },
                  }}
                />
              }
              label={
                <Box>
                  <Typography variant="body2">
                    Requiere autenticación
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    El servidor requiere credenciales para publicar
                  </Typography>
                </Box>
              }
            />

            {formData.auth_required && !server && (
              <Box sx={{ mt: 2 }}>
                <Alert severity="info" sx={{ mb: 2 }}>
                  Las credenciales se usarán solo para la configuración inicial
                </Alert>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <TextField
                      label="Usuario"
                      value={formData.username}
                      onChange={(e) =>
                        setFormData({ ...formData, username: e.target.value })
                      }
                      error={!!errors.username}
                      helperText={errors.username}
                      fullWidth
                      autoComplete="username"
                      slotProps={{
                        input: {
                          startAdornment: (
                            <InputAdornment position="start">
                              <LockIcon
                                sx={{ color: "action.active", fontSize: 20 }}
                              />
                            </InputAdornment>
                          ),
                        },
                      }}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <TextField
                      label="Contraseña"
                      type="password"
                      value={formData.password}
                      onChange={(e) =>
                        setFormData({ ...formData, password: e.target.value })
                      }
                      error={!!errors.password}
                      helperText={errors.password}
                      fullWidth
                      autoComplete="new-password"
                      slotProps={{
                        input: {
                          startAdornment: (
                            <InputAdornment position="start">
                              <LockIcon
                                sx={{ color: "action.active", fontSize: 20 }}
                              />
                            </InputAdornment>
                          ),
                        },
                      }}
                    />
                  </Grid>
                </Grid>
              </Box>
            )}

            {server && formData.auth_required && (
              <Alert severity="info" sx={{ mt: 2 }}>
                Para cambiar las credenciales, use el botón "Autenticar" después
                de guardar
              </Alert>
            )}
          </Box>
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 3, py: 2, bgcolor: "grey.50" }}>
        <Button onClick={onClose} disabled={loading} sx={{ mr: 1 }}>
          Cancelar
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading}
          startIcon={
            loading ? (
              <CircularProgress size={16} />
            ) : server ? (
              <EditIcon />
            ) : (
              <AddIcon />
            )
          }
          sx={{
            minWidth: 150,
            background: (theme) =>
              `linear-gradient(45deg, ${theme.palette.primary.main} 30%, ${theme.palette.primary.light} 90%)`,
            boxShadow: "0 3px 5px 2px rgba(33, 203, 243, .3)",
            "&:hover": {
              background: (theme) =>
                `linear-gradient(45deg, ${theme.palette.primary.dark} 30%, ${theme.palette.primary.main} 90%)`,
            },
          }}
        >
          {server ? "Guardar cambios" : "Agregar servidor"}
        </Button>
      </DialogActions>
    </Dialog>
  );
});

ServerFormDialog.displayName = "ServerFormDialog";

/**
 * Página de gestión de servidores MediaMTX
 */
const MediaMTXServersPage = memo(() => {
  const { remote, fetchRemoteServers } = usePublishingStore();
  const [formDialogOpen, setFormDialogOpen] = useState(false);
  const [authDialogOpen, setAuthDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedServer, setSelectedServer] = useState<MediaMTXServer | null>(
    null
  );
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [testingConnection, setTestingConnection] = useState<number | null>(
    null
  );

  // Hook para detectar usuarios nuevos
  const { shouldShowWizard, markOnboardingComplete } = useFirstTimeUser();

  // Cargar servidores al montar
  useEffect(() => {
    fetchRemoteServers();
  }, [fetchRemoteServers]);

  // Crear servidor
  const handleCreateServer = useCallback(
    async (data: ServerFormData) => {
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
        console.error("Error creando servidor:", error);
        throw error;
      }
    },
    [fetchRemoteServers]
  );

  // Actualizar servidor
  const handleUpdateServer = useCallback(
    async (data: ServerFormData) => {
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
        console.error("Error actualizando servidor:", error);
        throw error;
      }
    },
    [selectedServer, fetchRemoteServers]
  );

  // Eliminar servidor
  const handleDeleteServer = useCallback(async () => {
    if (!selectedServer) return;

    try {
      await mediamtxServerService.deleteServer(selectedServer.id);
      await fetchRemoteServers(); // Recargar lista
      setDeleteDialogOpen(false);
      setSelectedServer(null);
    } catch (error) {
      console.error("Error eliminando servidor:", error);
    }
  }, [selectedServer, fetchRemoteServers]);

  // Probar conexión
  const handleTestConnection = useCallback(async (server: MediaMTXServer) => {
    setTestingConnection(server.id);
    try {
      const result = await mediamtxServerService.testConnection(server.id);

      // Si requiere autenticación y no está autenticado, abrir diálogo
      // TODO: Verificar estructura de respuesta con backend
      if (
        (result as any).details?.auth_required &&
        !(result as any).details?.auth_status?.includes("Autenticado")
      ) {
        setSelectedServer(server);
        setAuthDialogOpen(true);
      }
    } catch (error) {
      console.error("Error probando conexión:", error);
    } finally {
      setTestingConnection(null);
    }
  }, []);

  // Abrir menú de acciones
  const handleOpenMenu = (
    event: React.MouseEvent<HTMLElement>,
    server: MediaMTXServer
  ) => {
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
      field: "name",
      headerName: "Nombre",
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
      field: "api_url",
      headerName: "URL del Servidor",
      flex: 1.5,
      renderCell: (row: MediaMTXServer) => (
        <Box>
          <Typography variant="body2" sx={{ fontFamily: "monospace" }}>
            {row.api_url}
          </Typography>
          <Box sx={{ display: "flex", gap: 0.5, mt: 0.5 }}>
            <Chip label="RTMP" size="small" variant="outlined" />
            <Chip label="RTSP" size="small" variant="outlined" />
          </Box>
        </Box>
      ),
    },
    {
      field: "status",
      headerName: "Estado",
      width: 200,
      renderCell: (row: MediaMTXServer) => (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            {row.is_active ? (
              <CheckIcon
                sx={{ fontSize: 20, color: colorTokens.status.connected }}
              />
            ) : (
              <WarningIcon
                sx={{ fontSize: 20, color: colorTokens.neutral[500] }}
              />
            )}
            <Typography variant="body2">
              {row.is_active ? "Activo" : "Inactivo"}
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
      field: "last_health_check",
      headerName: "Última verificación",
      width: 180,
      renderCell: (row: MediaMTXServer) => (
        <Typography variant="body2" color="text.secondary">
          {row.last_health_check
            ? new Date(row.last_health_check).toLocaleString("es-ES", {
                day: "2-digit",
                month: "short",
                hour: "2-digit",
                minute: "2-digit",
              })
            : "Nunca"}
        </Typography>
      ),
    },
    {
      field: "actions",
      headerName: "Acciones",
      width: 300,
      sortable: false,
      renderCell: (row: MediaMTXServer) => (
        <Box sx={{ display: "flex", gap: 1 }}>
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
          <IconButton size="small" onClick={(e) => handleOpenMenu(e, row)}>
            <MoreIcon />
          </IconButton>
        </Box>
      ),
    },
  ];

  return (
    <PageTransition variant="slideUp">
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Box>
          {/* Header */}
          <Box
            sx={{
              mb: 4,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <Box>
              <Typography variant="h4" gutterBottom>
                Servidores MediaMTX Remotos
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Gestiona los servidores MediaMTX remotos para publicación de
                cámaras a la nube
              </Typography>
            </Box>
            <Box sx={{ display: "flex", gap: 2 }}>
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

          {/* Panel informativo */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
          >
            <Card
              sx={{
                mb: 3,
                background: (theme) =>
                  theme.palette.mode === "dark"
                    ? "linear-gradient(135deg, rgba(33, 150, 243, 0.15) 0%, rgba(33, 150, 243, 0.05) 100%)"
                    : "linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)",
                border: "1px solid",
                borderColor: (theme) =>
                  theme.palette.mode === "dark"
                    ? "rgba(33, 150, 243, 0.3)"
                    : "primary.light",
              }}
            >
              <CardContent>
                <Box sx={{ display: "flex", alignItems: "flex-start", gap: 2 }}>
                  <InfoIcon
                    sx={{ color: "primary.main", fontSize: 28, mt: 0.5 }}
                  />
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h6" gutterBottom color="primary">
                      ¿Qué son los Servidores Remotos?
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 2 }}>
                      Los servidores remotos te permiten transmitir las cámaras
                      de tu red local hacia internet, haciéndolas accesibles
                      desde cualquier lugar del mundo de forma segura.
                    </Typography>
                    <Grid container spacing={3} sx={{ mt: 1 }}>
                      <Grid size={{ xs: 12, md: 4 }}>
                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 1,
                            mb: 1,
                          }}
                        >
                          <PublicIcon sx={{ color: "success.main" }} />
                          <Typography variant="subtitle2" fontWeight={600}>
                            Acceso Global
                          </Typography>
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          Ve tus cámaras desde cualquier dispositivo con
                          internet, sin configurar tu router.
                        </Typography>
                      </Grid>
                      <Grid size={{ xs: 12, md: 4 }}>
                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 1,
                            mb: 1,
                          }}
                        >
                          <LockIcon sx={{ color: "warning.main" }} />
                          <Typography variant="subtitle2" fontWeight={600}>
                            Seguridad
                          </Typography>
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          Conexión encriptada y autenticación para proteger tu
                          privacidad.
                        </Typography>
                      </Grid>
                      <Grid size={{ xs: 12, md: 4 }}>
                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 1,
                            mb: 1,
                          }}
                        >
                          <CloudIcon sx={{ color: "info.main" }} />
                          <Typography variant="subtitle2" fontWeight={600}>
                            Sin Configuración
                          </Typography>
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          No necesitas abrir puertos ni configurar DNS dinámico.
                        </Typography>
                      </Grid>
                    </Grid>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </motion.div>

          {/* Tabla de servidores */}
          {remote.isLoadingServers && remote.servers.length === 0 ? (
            <SkeletonTable rows={3} columns={3} />
          ) : (
            <Paper>
              <DataTable
                columns={columns}
                data={remote.servers}
                getRowId={(row: MediaMTXServer) => row.id.toString()}
                emptyMessage={
                  <Box sx={{ textAlign: "center", py: 2 }}>
                    <CloudIcon
                      sx={{ fontSize: 48, color: "text.disabled", mb: 2 }}
                    />
                    <Typography variant="h6" gutterBottom>
                      No hay servidores remotos configurados
                    </Typography>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mb: 3, maxWidth: 400, mx: "auto" }}
                    >
                      Configura tu primer servidor remoto para comenzar a
                      transmitir tus cámaras a internet y acceder a ellas desde
                      cualquier lugar.
                    </Typography>
                  </Box>
                }
                emptyAction={
                  <Button
                    variant="contained"
                    size="large"
                    startIcon={<AddIcon />}
                    onClick={() => {
                      setSelectedServer(null);
                      setFormDialogOpen(true);
                    }}
                  >
                    Configurar Primer Servidor
                  </Button>
                }
              />
            </Paper>
          )}

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
              sx={{ color: "error.main" }}
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
            <ServerAuthDialog
              open={authDialogOpen}
              server={{
                id: selectedServer.id,
                name: selectedServer.name || selectedServer.server_name || "",
                apiUrl: selectedServer.api_url,
                isAuthenticated: selectedServer.is_authenticated,
                lastAuthError: undefined,
              }}
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

          {/* Wizard de bienvenida para usuarios nuevos */}
          <WelcomeWizard
            open={shouldShowWizard}
            onClose={() => markOnboardingComplete()}
            onComplete={() => {
              markOnboardingComplete();
              fetchRemoteServers(); // Recargar servidores después del wizard
            }}
          />
        </Box>
      </Container>
    </PageTransition>
  );
});

MediaMTXServersPage.displayName = "MediaMTXServersPage";

export default MediaMTXServersPage;
