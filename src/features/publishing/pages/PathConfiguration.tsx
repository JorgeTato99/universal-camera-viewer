/**
 * 🛤️ Path Configuration Page - Universal Camera Viewer
 * Configuración de paths y servidores MediaMTX
 */

import React, { useState, useEffect, memo } from "react";
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  Fade,
  CircularProgress,
  Alert,
  Tooltip,
  Divider,
} from "@mui/material";
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as TestIcon,
  CheckCircle as ActiveIcon,
  RadioButtonUnchecked as InactiveIcon,
} from "@mui/icons-material";
import { usePublishingStore } from "../../../stores/publishingStore";
import { PublishConfiguration, CreateConfigurationRequest } from "../types";
import { validateMediaMTXUrl } from "../utils";

/**
 * Página de configuración de paths MediaMTX
 */
const PathConfiguration = memo(() => {
  const {
    configurations,
    activeConfig,
    isLoading,
    error,
    fetchConfigurations,
    createConfiguration,
    updateConfiguration,
    deleteConfiguration,
    activateConfiguration,
    clearError,
  } = usePublishingStore();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingConfig, setEditingConfig] =
    useState<PublishConfiguration | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
  const [testingConfigId, setTestingConfigId] = useState<number | null>(null);

  // Estado del formulario
  const [formData, setFormData] = useState<Partial<CreateConfigurationRequest>>(
    {
      name: "",
      mediamtx_url: "",
      api_url: "",
      api_enabled: false,
      username: "",
      password: "",
      auth_enabled: false,
      use_tcp: true,
      max_reconnects: 3,
      reconnect_delay: 5.0,
      publish_path_template: "camera_{camera_id}",
    }
  );

  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Cargar configuraciones al montar
  useEffect(() => {
    fetchConfigurations();
  }, [fetchConfigurations]);

  // Limpiar error al desmontar
  useEffect(() => {
    return () => clearError();
  }, [clearError]);

  // Abrir diálogo para nueva configuración
  const handleNewConfig = () => {
    setEditingConfig(null);
    setFormData({
      name: "",
      mediamtx_url: "",
      api_url: "",
      api_enabled: false,
      username: "",
      password: "",
      auth_enabled: false,
      use_tcp: true,
      max_reconnects: 3,
      reconnect_delay: 5.0,
      publish_path_template: "camera_{camera_id}",
    });
    setFormErrors({});
    setDialogOpen(true);
  };

  // Abrir diálogo para editar
  const handleEditConfig = (config: PublishConfiguration) => {
    setEditingConfig(config);
    setFormData({
      name: config.name,
      mediamtx_url: config.mediamtx_url,
      api_url: config.api_url || "",
      api_enabled: config.api_enabled,
      username: config.username || "",
      password: "", // No mostrar password existente
      auth_enabled: config.auth_enabled,
      use_tcp: config.use_tcp,
      max_reconnects: config.max_reconnects,
      reconnect_delay: config.reconnect_delay,
      publish_path_template: config.publish_path_template,
    });
    setFormErrors({});
    setDialogOpen(true);
  };

  // Validar formulario
  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.name?.trim()) {
      errors.name = "El nombre es requerido";
    }

    if (!formData.mediamtx_url?.trim()) {
      errors.mediamtx_url = "La URL de MediaMTX es requerida";
    } else if (!validateMediaMTXUrl(formData.mediamtx_url)) {
      errors.mediamtx_url =
        "URL inválida (debe ser rtsp://, rtmp://, http:// o https://)";
    }

    if (formData.api_enabled && !formData.api_url?.trim()) {
      errors.api_url = "La URL de API es requerida cuando está habilitada";
    }

    if (formData.auth_enabled) {
      if (!formData.username?.trim()) {
        errors.username =
          "El usuario es requerido cuando la autenticación está habilitada";
      }
      if (!editingConfig && !formData.password?.trim()) {
        errors.password =
          "La contraseña es requerida para configuraciones nuevas";
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Guardar configuración
  const handleSave = async () => {
    if (!validateForm()) return;

    try {
      if (editingConfig) {
        await updateConfiguration(editingConfig.id, formData);
      } else {
        await createConfiguration(formData);
      }
      setDialogOpen(false);
    } catch (error) {
      // El error ya se maneja en el store
    }
  };

  // Eliminar configuración
  const handleDelete = async (id: number) => {
    try {
      await deleteConfiguration(id);
      setDeleteConfirmId(null);
    } catch (error) {
      // El error ya se maneja en el store
    }
  };

  // Activar configuración
  const handleActivate = async (name: string) => {
    try {
      await activateConfiguration(name);
    } catch (error) {
      // El error ya se maneja en el store
    }
  };

  // Probar configuración
  const handleTest = async (id: number) => {
    setTestingConfigId(id);
    // TODO: Implementar test real
    setTimeout(() => {
      setTestingConfigId(null);
    }, 2000);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Fade in timeout={300}>
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
                Configuración de Servidores
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Gestión de configuraciones MediaMTX para publicación
              </Typography>
            </Box>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleNewConfig}
            >
              Nueva Configuración
            </Button>
          </Box>

          {/* Error global */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }} onClose={clearError}>
              {error}
            </Alert>
          )}

          {/* Grid de configuraciones */}
          {isLoading ? (
            <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
              <CircularProgress />
            </Box>
          ) : configurations.length === 0 ? (
            <Paper sx={{ p: 6, textAlign: "center" }}>
              <Typography variant="body1" color="text.secondary" gutterBottom>
                No hay configuraciones de servidor
              </Typography>
              <Button
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={handleNewConfig}
                sx={{ mt: 2 }}
              >
                Crear Primera Configuración
              </Button>
            </Paper>
          ) : (
            <Grid container spacing={3}>
              {configurations.map((config) => (
                <Grid key={config.id} size={{ xs: 12, md: 6, lg: 4 }}>
                  <Card
                    sx={{
                      height: "100%",
                      display: "flex",
                      flexDirection: "column",
                      borderColor: config.is_active
                        ? "primary.main"
                        : "divider",
                      borderWidth: config.is_active ? 2 : 1,
                      borderStyle: "solid",
                    }}
                  >
                    <CardContent sx={{ flex: 1 }}>
                      <Box
                        sx={{ display: "flex", alignItems: "center", mb: 2 }}
                      >
                        <Typography variant="h6" sx={{ flex: 1 }}>
                          {config.name}
                        </Typography>
                        {config.is_active && (
                          <Chip
                            icon={<ActiveIcon />}
                            label="Activa"
                            color="primary"
                            size="small"
                          />
                        )}
                      </Box>

                      <Typography
                        variant="body2"
                        color="text.secondary"
                        gutterBottom
                      >
                        <strong>URL:</strong> {config.mediamtx_url}
                      </Typography>

                      <Typography
                        variant="body2"
                        color="text.secondary"
                        gutterBottom
                      >
                        <strong>Protocolo:</strong>{" "}
                        {config.use_tcp ? "TCP" : "UDP"}
                      </Typography>

                      <Typography
                        variant="body2"
                        color="text.secondary"
                        gutterBottom
                      >
                        <strong>Autenticación:</strong>{" "}
                        {config.auth_enabled ? "Sí" : "No"}
                      </Typography>

                      <Typography variant="body2" color="text.secondary">
                        <strong>Reintentos:</strong> {config.max_reconnects}{" "}
                        cada {config.reconnect_delay}s
                      </Typography>

                      {config.api_enabled && (
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{ mt: 1 }}
                        >
                          <strong>API:</strong> {config.api_url}
                        </Typography>
                      )}
                    </CardContent>

                    <Divider />

                    <CardActions
                      sx={{ justifyContent: "space-between", px: 2 }}
                    >
                      <Box>
                        {!config.is_active && (
                          <Tooltip title="Activar configuración">
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={() => handleActivate(config.name)}
                            >
                              <InactiveIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                        <Tooltip title="Probar conexión">
                          <IconButton
                            size="small"
                            onClick={() => handleTest(config.id)}
                            disabled={testingConfigId === config.id}
                          >
                            {testingConfigId === config.id ? (
                              <CircularProgress size={18} />
                            ) : (
                              <TestIcon />
                            )}
                          </IconButton>
                        </Tooltip>
                      </Box>
                      <Box>
                        <Tooltip title="Editar">
                          <IconButton
                            size="small"
                            onClick={() => handleEditConfig(config)}
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Eliminar">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => setDeleteConfirmId(config.id)}
                            disabled={config.is_active}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}

          {/* Diálogo de formulario */}
          <Dialog
            open={dialogOpen}
            onClose={() => setDialogOpen(false)}
            maxWidth="sm"
            fullWidth
          >
            <DialogTitle>
              {editingConfig ? "Editar Configuración" : "Nueva Configuración"}
            </DialogTitle>
            <DialogContent>
              <Box
                sx={{ pt: 2, display: "flex", flexDirection: "column", gap: 2 }}
              >
                <TextField
                  label="Nombre"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, name: e.target.value }))
                  }
                  error={!!formErrors.name}
                  helperText={formErrors.name}
                  fullWidth
                  required
                />

                <TextField
                  label="URL MediaMTX"
                  value={formData.mediamtx_url}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      mediamtx_url: e.target.value,
                    }))
                  }
                  error={!!formErrors.mediamtx_url}
                  helperText={
                    formErrors.mediamtx_url || "Ejemplo: rtsp://localhost:8554"
                  }
                  fullWidth
                  required
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.use_tcp}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          use_tcp: e.target.checked,
                        }))
                      }
                    />
                  }
                  label="Usar TCP (más confiable pero más lento)"
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.auth_enabled}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          auth_enabled: e.target.checked,
                        }))
                      }
                    />
                  }
                  label="Requiere autenticación"
                />

                {formData.auth_enabled && (
                  <>
                    <TextField
                      label="Usuario"
                      value={formData.username}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          username: e.target.value,
                        }))
                      }
                      error={!!formErrors.username}
                      helperText={formErrors.username}
                      fullWidth
                    />

                    <TextField
                      label={
                        editingConfig
                          ? "Nueva Contraseña (dejar vacío para mantener)"
                          : "Contraseña"
                      }
                      type="password"
                      value={formData.password}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          password: e.target.value,
                        }))
                      }
                      error={!!formErrors.password}
                      helperText={formErrors.password}
                      fullWidth
                      required={!editingConfig}
                    />
                  </>
                )}

                <TextField
                  label="Máximo de reintentos"
                  type="number"
                  value={formData.max_reconnects}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      max_reconnects: parseInt(e.target.value),
                    }))
                  }
                  inputProps={{ min: 0, max: 10 }}
                  fullWidth
                />

                <TextField
                  label="Delay entre reintentos (segundos)"
                  type="number"
                  value={formData.reconnect_delay}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      reconnect_delay: parseFloat(e.target.value),
                    }))
                  }
                  inputProps={{ min: 1, max: 60, step: 0.5 }}
                  fullWidth
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.api_enabled}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          api_enabled: e.target.checked,
                        }))
                      }
                    />
                  }
                  label="Habilitar API MediaMTX"
                />

                {formData.api_enabled && (
                  <TextField
                    label="URL API"
                    value={formData.api_url}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        api_url: e.target.value,
                      }))
                    }
                    error={!!formErrors.api_url}
                    helperText={
                      formErrors.api_url || "Ejemplo: http://localhost:9997"
                    }
                    fullWidth
                  />
                )}

                <TextField
                  label="Plantilla de Path"
                  value={formData.publish_path_template}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      publish_path_template: e.target.value,
                    }))
                  }
                  helperText="Variables disponibles: {camera_id}, {timestamp}, {random}"
                  fullWidth
                />
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDialogOpen(false)}>Cancelar</Button>
              <Button onClick={handleSave} variant="contained">
                {editingConfig ? "Actualizar" : "Crear"}
              </Button>
            </DialogActions>
          </Dialog>

          {/* Diálogo de confirmación de eliminación */}
          <Dialog
            open={deleteConfirmId !== null}
            onClose={() => setDeleteConfirmId(null)}
            maxWidth="xs"
            fullWidth
          >
            <DialogTitle>Confirmar Eliminación</DialogTitle>
            <DialogContent>
              <Typography>
                ¿Estás seguro de que deseas eliminar esta configuración?
              </Typography>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDeleteConfirmId(null)}>Cancelar</Button>
              <Button
                onClick={() => deleteConfirmId && handleDelete(deleteConfirmId)}
                color="error"
                variant="contained"
              >
                Eliminar
              </Button>
            </DialogActions>
          </Dialog>
        </Box>
      </Fade>
    </Container>
  );
});

PathConfiguration.displayName = "PathConfiguration";

export default PathConfiguration;
