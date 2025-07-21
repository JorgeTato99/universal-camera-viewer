/**
 * 📊 Publishing Metrics Page - Universal Camera Viewer
 * Métricas y estadísticas de publicación en tiempo real
 */

import React, { useState, useEffect, memo } from "react";
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  ToggleButtonGroup,
  ToggleButton,
  Card,
  CardContent,
  CircularProgress,
  Fade,
  Button,
  Menu,
  ListItemIcon,
  ListItemText,
} from "@mui/material";
import {
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  People as PeopleIcon,
  Storage as StorageIcon,
  GetApp as DownloadIcon,
  Description as CsvIcon,
  TableChart as ExcelIcon,
} from "@mui/icons-material";
import { usePublishingStore } from "../../../stores/publishingStore";
import { useCameraStoreV2 } from "../../../stores/cameraStore.v2";
import { usePublishingMetrics } from "../hooks/usePublishingMetrics";
import { formatBitrate, formatBytes, formatDuration } from "../utils";
import { colorTokens } from "../../../design-system/tokens";

/**
 * Página de métricas y estadísticas de publicación
 */
const PublishingMetrics = memo(() => {
  const { cameras, loadCameras } = useCameraStoreV2();
  const { activePublications, getPublicationByCameraId } = usePublishingStore();

  const [selectedCameraId, setSelectedCameraId] = useState<string>("");
  const [timeRange, setTimeRange] = useState<string>("last_hour");
  const [exportMenuAnchor, setExportMenuAnchor] = useState<null | HTMLElement>(
    null
  );

  // Hook de métricas para la cámara seleccionada
  const { metrics, latestMetric, stats, isLoading, isActive } =
    usePublishingMetrics({
      cameraId: selectedCameraId,
      autoRefresh: true,
      refreshInterval: 5,
      maxSamples: 100,
    });

  // Cargar cámaras al montar
  useEffect(() => {
    loadCameras();
  }, [loadCameras]);

  // Auto-seleccionar primera cámara activa
  useEffect(() => {
    if (!selectedCameraId && activePublications.size > 0) {
      const firstActive = Array.from(activePublications.values())[0];
      setSelectedCameraId(firstActive.camera_id);
    }
  }, [activePublications, selectedCameraId]);

  // Obtener lista de cámaras con publicación
  const camerasWithPublication = Array.from(cameras.values()).filter((camera) =>
    activePublications.has(camera.camera_id)
  );

  // Manejar exportación
  const handleExport = (format: "csv" | "excel") => {
    setExportMenuAnchor(null);
    // TODO: Implementar exportación real
    console.log(`Exportando en formato ${format}`);
  };

  const selectedCamera = selectedCameraId
    ? cameras.get(selectedCameraId)
    : null;
  const publication = selectedCameraId
    ? getPublicationByCameraId(selectedCameraId)
    : undefined;

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Fade in timeout={300}>
        <Box>
          {/* Header */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h4" gutterBottom>
              Métricas de Publicación
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Estadísticas en tiempo real y análisis de rendimiento
            </Typography>
          </Box>

          {/* Controles */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Grid container spacing={3} alignItems="center">
              <Grid size={{ xs: 12, md: 4 }}>
                <FormControl fullWidth>
                  <InputLabel>Seleccionar Cámara</InputLabel>
                  <Select
                    value={selectedCameraId}
                    onChange={(e) => setSelectedCameraId(e.target.value)}
                    label="Seleccionar Cámara"
                  >
                    {camerasWithPublication.length === 0 ? (
                      <MenuItem disabled>No hay cámaras publicando</MenuItem>
                    ) : (
                      camerasWithPublication.map((camera) => (
                        <MenuItem
                          key={camera.camera_id}
                          value={camera.camera_id}
                        >
                          {camera.display_name} ({camera.ip_address})
                        </MenuItem>
                      ))
                    )}
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <ToggleButtonGroup
                  value={timeRange}
                  exclusive
                  onChange={(_, value) => value && setTimeRange(value)}
                  size="small"
                  fullWidth
                >
                  <ToggleButton value="last_hour">1H</ToggleButton>
                  <ToggleButton value="last_6_hours">6H</ToggleButton>
                  <ToggleButton value="last_24_hours">24H</ToggleButton>
                  <ToggleButton value="last_7_days">7D</ToggleButton>
                </ToggleButtonGroup>
              </Grid>
              <Grid
                size={{ xs: 12, md: 4 }}
                sx={{ display: "flex", justifyContent: "flex-end" }}
              >
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={(e) => setExportMenuAnchor(e.currentTarget)}
                  disabled={!selectedCameraId || metrics.length === 0}
                >
                  Exportar
                </Button>
                <Menu
                  anchorEl={exportMenuAnchor}
                  open={Boolean(exportMenuAnchor)}
                  onClose={() => setExportMenuAnchor(null)}
                >
                  <MenuItem onClick={() => handleExport("csv")}>
                    <ListItemIcon>
                      <CsvIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText>Exportar como CSV</ListItemText>
                  </MenuItem>
                  <MenuItem onClick={() => handleExport("excel")}>
                    <ListItemIcon>
                      <ExcelIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText>Exportar como Excel</ListItemText>
                  </MenuItem>
                </Menu>
              </Grid>
            </Grid>
          </Paper>

          {/* Contenido principal */}
          {!selectedCameraId ? (
            <Paper sx={{ p: 6, textAlign: "center" }}>
              <Typography variant="body1" color="text.secondary">
                Selecciona una cámara para ver sus métricas
              </Typography>
            </Paper>
          ) : !isActive ? (
            <Paper sx={{ p: 6, textAlign: "center" }}>
              <Typography variant="body1" color="text.secondary">
                La cámara seleccionada no está publicando actualmente
              </Typography>
            </Paper>
          ) : (
            <>
              {/* Cards de estadísticas */}
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Card>
                    <CardContent>
                      <Box
                        sx={{ display: "flex", alignItems: "center", mb: 2 }}
                      >
                        <TimelineIcon
                          sx={{ color: colorTokens.primary[500], mr: 1 }}
                        />
                        <Typography variant="subtitle2" color="text.secondary">
                          FPS Actual
                        </Typography>
                      </Box>
                      <Typography variant="h4">
                        {latestMetric?.fps || 0}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Promedio: {stats.avgFps} | Max: {stats.maxFps}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Card>
                    <CardContent>
                      <Box
                        sx={{ display: "flex", alignItems: "center", mb: 2 }}
                      >
                        <SpeedIcon
                          sx={{ color: colorTokens.secondary[500], mr: 1 }}
                        />
                        <Typography variant="subtitle2" color="text.secondary">
                          Bitrate
                        </Typography>
                      </Box>
                      <Typography variant="h4">
                        {formatBitrate(latestMetric?.bitrate_kbps || 0)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Promedio: {formatBitrate(stats.avgBitrate)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Card>
                    <CardContent>
                      <Box
                        sx={{ display: "flex", alignItems: "center", mb: 2 }}
                      >
                        <PeopleIcon
                          sx={{ color: colorTokens.alert.info, mr: 1 }}
                        />
                        <Typography variant="subtitle2" color="text.secondary">
                          Viewers
                        </Typography>
                      </Box>
                      <Typography variant="h4">
                        {latestMetric?.viewers || 0}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Activos ahora mismo
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Card>
                    <CardContent>
                      <Box
                        sx={{ display: "flex", alignItems: "center", mb: 2 }}
                      >
                        <StorageIcon
                          sx={{ color: colorTokens.alert.warning, mr: 1 }}
                        />
                        <Typography variant="subtitle2" color="text.secondary">
                          Datos Transferidos
                        </Typography>
                      </Box>
                      <Typography variant="h4">
                        {formatBytes(stats.totalData)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        En {metrics.length} muestras
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Gráficos (placeholder) */}
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, lg: 8 }}>
                  <Paper sx={{ p: 3, height: 400 }}>
                    <Typography variant="h6" gutterBottom>
                      Métricas en Tiempo Real
                    </Typography>
                    <Box
                      sx={{
                        display: "flex",
                        justifyContent: "center",
                        alignItems: "center",
                        height: "calc(100% - 40px)",
                        color: "text.secondary",
                      }}
                    >
                      {isLoading ? (
                        <CircularProgress />
                      ) : (
                        <Typography variant="body2">
                          Gráfico de líneas con FPS, Bitrate y Viewers
                          próximamente...
                        </Typography>
                      )}
                    </Box>
                  </Paper>
                </Grid>

                <Grid size={{ xs: 12, lg: 4 }}>
                  <Paper sx={{ p: 3, height: 400 }}>
                    <Typography variant="h6" gutterBottom>
                      Información de Sesión
                    </Typography>
                    {publication && selectedCamera && (
                      <Box sx={{ mt: 2 }}>
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="caption" color="text.secondary">
                            Cámara
                          </Typography>
                          <Typography variant="body2">
                            {selectedCamera.display_name}
                          </Typography>
                        </Box>
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="caption" color="text.secondary">
                            Tiempo Activo
                          </Typography>
                          <Typography variant="body2">
                            {formatDuration(publication.uptime_seconds)}
                          </Typography>
                        </Box>
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="caption" color="text.secondary">
                            Path de Publicación
                          </Typography>
                          <Typography
                            variant="body2"
                            sx={{ fontFamily: "monospace" }}
                          >
                            {publication.publish_path}
                          </Typography>
                        </Box>
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="caption" color="text.secondary">
                            Errores
                          </Typography>
                          <Typography variant="body2">
                            {publication.error_count}
                          </Typography>
                        </Box>
                      </Box>
                    )}
                  </Paper>
                </Grid>
              </Grid>
            </>
          )}
        </Box>
      </Fade>
    </Container>
  );
});

PublishingMetrics.displayName = "PublishingMetrics";

export default PublishingMetrics;
