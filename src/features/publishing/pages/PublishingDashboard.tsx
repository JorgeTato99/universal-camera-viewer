/**
 * 📊 Publishing Dashboard - Universal Camera Viewer
 * Panel principal de control para publicaciones MediaMTX
 */

import { useEffect, memo, useState, useCallback } from "react";
import {
  Box,
  Container,
  Typography,
  Grid,
  Paper,
  Fade,
  CircularProgress,
  alpha,
  Tooltip,
  Tabs,
  Tab,
  Button,
  Chip,
  Fab,
  Badge,
  Zoom,
} from "@mui/material";
import {
  HelpOutline as HelpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  CloudQueue as CloudIcon,
  Computer as LocalIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  Videocam as PublishIcon,
} from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import { usePublishingHealth } from "../hooks/usePublishingHealth";
import { usePublishingStore } from "../../../stores/publishingStore";
import { useCameraStoreV2 } from "../../../stores/cameraStore.v2";
import { ConnectionStatus } from "../../../types/camera.types.v2";
import { colorTokens } from "../../../design-system/tokens";
import { initializePublishingWebSocket } from "../../../services/websocket/publishingWebSocket";
import { PublishCameraModal } from "../components/PublishCameraModal";

/**
 * Dashboard principal de publicación MediaMTX
 */
const PublishingDashboard = memo(() => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(0);
  const [publishModalOpen, setPublishModalOpen] = useState(false);
  
  const {
    systemHealth,
    healthIndicators,
    alerts,
    isLoading,
    refresh,
  } = usePublishingHealth({
    autoRefresh: true,
    refreshInterval: 30,
  });

  const { 
    configurations, 
    fetchConfigurations,
    remote,
    unifiedMetrics,
    fetchRemoteServers,
    fetchUnifiedPublications,
  } = usePublishingStore();

  const { cameras, loadCameras } = useCameraStoreV2();

  // Inicializar WebSocket y cargar datos al montar
  useEffect(() => {
    // Iniciar WebSocket para eventos en tiempo real
    initializePublishingWebSocket();
    
    // Cargar datos iniciales
    fetchConfigurations();
    fetchRemoteServers();
    fetchUnifiedPublications();
    loadCameras();
  }, [fetchConfigurations, fetchRemoteServers, fetchUnifiedPublications, loadCameras]);

  // Calcular cámaras disponibles para publicar
  const availableCamerasCount = Array.from(cameras.values()).filter(
    camera => camera.status === ConnectionStatus.CONNECTED
  ).length;

  // Handlers
  const handlePublishSuccess = useCallback((cameraId: string, serverId: number) => {
    // Navegar a publicaciones activas después de publicar
    navigate('/publishing/active');
  }, [navigate]);
  
  // Actualizar datos según el tab activo
  useEffect(() => {
    if (activeTab === 0) {
      // Tab de servidores remotos
      fetchRemoteServers();
    }
  }, [activeTab, fetchRemoteServers]);

  // Mostrar loader mientras carga
  if (isLoading && !systemHealth) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "400px",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Fade in timeout={300}>
        <Box>
          {/* Header con acciones */}
          <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <Box>
              <Typography variant="h4" gutterBottom>
                Dashboard de Publicación
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Panel de control para servidores MediaMTX locales y remotos
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={() => {
                  refresh();
                  fetchUnifiedPublications();
                }}
              >
                Actualizar
              </Button>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => navigate('/publishing/servers')}
              >
                Agregar Servidor
              </Button>
            </Box>
          </Box>
          
          {/* Tabs para separar contextos */}
          <Paper sx={{ mb: 3 }}>
            <Tabs 
              value={activeTab} 
              onChange={(_, newValue) => setActiveTab(newValue)}
              sx={{ borderBottom: 1, borderColor: 'divider' }}
            >
              <Tab 
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CloudIcon fontSize="small" />
                    <span>Servidores Remotos</span>
                    <Chip 
                      label={remote.servers.length} 
                      size="small" 
                      color={remote.servers.length > 0 ? "primary" : "default"}
                    />
                  </Box>
                } 
              />
              <Tab 
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LocalIcon fontSize="small" />
                    <span>Servidor Local</span>
                    {configurations.find(c => c.is_active) && (
                      <Chip label="Activo" size="small" color="success" />
                    )}
                  </Box>
                } 
              />
            </Tabs>
          </Paper>

          {/* Grid de widgets */}
          <Grid container spacing={3}>
            {/* Widget de Salud del Sistema */}
            <Grid size={{ xs: 12, md: 6, lg: 3 }}>
              <Paper
                sx={{
                  p: 3,
                  height: "100%",
                  borderLeft: 6,
                  borderColor: healthIndicators.isHealthy
                    ? colorTokens.status.connected
                    : healthIndicators.hasErrors
                    ? colorTokens.status.error
                    : colorTokens.alert.warning,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Typography
                    variant="subtitle2"
                    color="text.secondary"
                    gutterBottom
                  >
                    Estado del Sistema
                  </Typography>
                  <Tooltip 
                    title="Estado general de todos los servidores MediaMTX configurados. Saludable = todos los servidores funcionando correctamente" 
                    arrow 
                    placement="top"
                  >
                    <HelpIcon sx={{ fontSize: 16, cursor: 'help', color: 'action.disabled', mb: 1 }} />
                  </Tooltip>
                </Box>
                <Typography variant="h4" sx={{ mb: 1 }}>
                  {systemHealth?.overall_status === "healthy"
                    ? "✅ Saludable"
                    : systemHealth?.overall_status === "warning"
                    ? "⚠️ Advertencia"
                    : systemHealth?.overall_status === "error"
                    ? "❌ Error"
                    : "⏳ Verificando..."}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {systemHealth?.healthy_servers || 0} de{" "}
                  {systemHealth?.total_servers || 0} servidores activos
                </Typography>
              </Paper>
            </Grid>

            {/* Widget de Publicaciones Activas */}
            <Grid size={{ xs: 12, md: 6, lg: 3 }}>
              <Paper
                sx={{
                  p: 3,
                  height: "100%",
                  borderLeft: 6,
                  borderColor: colorTokens.primary[500],
                }}
              >
                <Typography
                  variant="subtitle2"
                  color="text.secondary"
                  gutterBottom
                >
                  Publicaciones Activas
                </Typography>
                <Typography variant="h4" sx={{ mb: 1 }}>
                  {unifiedMetrics.totalPublications}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {unifiedMetrics.localPublications} locales • {unifiedMetrics.remotePublications} remotas
                </Typography>
              </Paper>
            </Grid>

            {/* Widget de Viewers Totales */}
            <Grid size={{ xs: 12, md: 6, lg: 3 }}>
              <Paper
                sx={{
                  p: 3,
                  height: "100%",
                  borderLeft: 6,
                  borderColor: colorTokens.secondary[500],
                }}
              >
                <Typography
                  variant="subtitle2"
                  color="text.secondary"
                  gutterBottom
                >
                  Viewers Totales
                </Typography>
                <Typography variant="h4" sx={{ mb: 1 }}>
                  {unifiedMetrics.totalViewers}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {unifiedMetrics.totalBandwidthMbps.toFixed(1)} Mbps total
                </Typography>
              </Paper>
            </Grid>

            {/* Widget de Alertas */}
            <Grid size={{ xs: 12, md: 6, lg: 3 }}>
              <Paper
                sx={{
                  p: 3,
                  height: "100%",
                  borderLeft: 6,
                  borderColor:
                    healthIndicators.activeAlerts.length > 0
                      ? colorTokens.alert.error
                      : colorTokens.neutral[300],
                }}
              >
                <Typography
                  variant="subtitle2"
                  color="text.secondary"
                  gutterBottom
                >
                  Alertas Activas
                </Typography>
                <Typography variant="h4" sx={{ mb: 1 }}>
                  {healthIndicators.activeAlerts.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {healthIndicators.activeAlerts.filter(
                    (a) => a.severity === "critical"
                  ).length > 0 &&
                    `${
                      healthIndicators.activeAlerts.filter(
                        (a) => a.severity === "critical"
                      ).length
                    } críticas`}
                  {healthIndicators.activeAlerts.length === 0 &&
                    "Sin alertas pendientes"}
                </Typography>
              </Paper>
            </Grid>

            {/* Gráfico de Viewers (placeholder por ahora) */}
            <Grid size={{ xs: 12, lg: 8 }}>
              <Paper sx={{ p: 3, height: "400px" }}>
                <Typography variant="h6" gutterBottom>
                  Viewers en las Últimas 24 Horas
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
                  <Typography variant="body2">
                    Gráfico de línea temporal próximamente...
                  </Typography>
                </Box>
              </Paper>
            </Grid>

            {/* Lista de Alertas */}
            <Grid size={{ xs: 12, lg: 4 }}>
              <Paper sx={{ p: 3, height: "400px", overflow: "auto" }}>
                <Typography variant="h6" gutterBottom>
                  Alertas Recientes
                </Typography>
                {alerts.length === 0 ? (
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "center",
                      alignItems: "center",
                      height: "calc(100% - 40px)",
                      color: "text.secondary",
                    }}
                  >
                    <Typography variant="body2">
                      No hay alertas activas
                    </Typography>
                  </Box>
                ) : (
                  <Box
                    sx={{ display: "flex", flexDirection: "column", gap: 2 }}
                  >
                    {alerts.slice(0, 5).map((alert) => (
                      <Box
                        key={alert.id}
                        sx={{
                          p: 2,
                          borderRadius: 1,
                          bgcolor:
                            alert.severity === "critical"
                              ? alpha(colorTokens.alert.error, 0.1)
                              : alert.severity === "error"
                              ? alpha(colorTokens.alert.error, 0.08)
                              : alert.severity === "warning"
                              ? alpha(colorTokens.alert.warning, 0.08)
                              : alpha(colorTokens.alert.info, 0.08),
                          borderLeft: 4,
                          borderColor:
                            alert.severity === "critical"
                              ? colorTokens.alert.error
                              : alert.severity === "error"
                              ? colorTokens.alert.error
                              : alert.severity === "warning"
                              ? colorTokens.alert.warning
                              : colorTokens.alert.info,
                        }}
                      >
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {alert.severity === "critical" && "🚨 "}
                          {alert.severity === "error" && "❌ "}
                          {alert.severity === "warning" && "⚠️ "}
                          {alert.severity === "info" && "ℹ️ "}
                          {alert.message}
                        </Typography>
                        {alert.camera_id && (
                          <Typography variant="caption" color="text.secondary">
                            Cámara: {alert.camera_id}
                          </Typography>
                        )}
                      </Box>
                    ))}
                  </Box>
                )}
              </Paper>
            </Grid>

            {/* Contenido específico por tab */}
            <Grid size={12}>
              {activeTab === 0 ? (
                /* Tab de Servidores Remotos */
                <Paper sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                    <Typography variant="h6">
                      Servidores MediaMTX Remotos
                    </Typography>
                    <Button
                      size="small"
                      onClick={() => navigate('/publishing/servers')}
                    >
                      Ver todos
                    </Button>
                  </Box>
                  
                  {remote.isLoadingServers ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                      <CircularProgress size={32} />
                    </Box>
                  ) : remote.servers.length === 0 ? (
                    <Box sx={{ textAlign: 'center', py: 6 }}>
                      <CloudIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                      <Typography variant="h6" color="text.secondary" gutterBottom>
                        No hay servidores remotos configurados
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        Agrega un servidor MediaMTX remoto para comenzar a publicar cámaras
                      </Typography>
                      <Button
                        variant="contained"
                        startIcon={<AddIcon />}
                        onClick={() => navigate('/publishing/servers')}
                      >
                        Configurar Primer Servidor
                      </Button>
                    </Box>
                  ) : (
                    <Grid container spacing={2}>
                      {remote.servers.slice(0, 6).map((server) => (
                        <Grid size={{ xs: 12, sm: 6, md: 4 }} key={server.id}>
                          <Box
                            sx={{
                              p: 2,
                              border: 1,
                              borderColor: server.is_authenticated
                                ? colorTokens.status.connected
                                : "divider",
                              borderRadius: 1,
                              bgcolor: server.is_authenticated
                                ? alpha(colorTokens.status.connected, 0.05)
                                : "transparent",
                              cursor: 'pointer',
                              transition: 'all 0.2s',
                              '&:hover': {
                                borderColor: colorTokens.primary[500],
                                bgcolor: alpha(colorTokens.primary[500], 0.05),
                              }
                            }}
                            onClick={() => navigate('/publishing/servers')}
                          >
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 1 }}>
                              <Typography variant="subtitle2">
                                {server.name}
                              </Typography>
                              {server.is_authenticated ? (
                                <CheckIcon sx={{ fontSize: 20, color: colorTokens.status.connected }} />
                              ) : (
                                <WarningIcon sx={{ fontSize: 20, color: colorTokens.alert.warning }} />
                              )}
                            </Box>
                            <Typography variant="caption" color="text.secondary" display="block">
                              {server.api_url}
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                              <Chip 
                                label={server.is_authenticated ? "Autenticado" : "Sin autenticar"}
                                size="small"
                                color={server.is_authenticated ? "success" : "default"}
                              />
                              {server.is_active && (
                                <Chip label="Activo" size="small" color="primary" />
                              )}
                            </Box>
                          </Box>
                        </Grid>
                      ))}
                    </Grid>
                  )}
                </Paper>
              ) : (
                /* Tab de Servidor Local */
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Configuración de Servidor Local
                  </Typography>
                  <Grid container spacing={2}>
                    {configurations.length === 0 ? (
                      <Grid size={12}>
                        <Box sx={{ textAlign: 'center', py: 6 }}>
                          <LocalIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                          <Typography variant="h6" color="text.secondary" gutterBottom>
                            No hay configuración local
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                            Configura un servidor MediaMTX local para publicar cámaras
                          </Typography>
                          <Button
                            variant="outlined"
                            onClick={() => navigate('/publishing/config')}
                          >
                            Configurar Servidor Local
                          </Button>
                        </Box>
                      </Grid>
                    ) : (
                      configurations.map((config) => (
                        <Grid size={{ xs: 12, sm: 6, md: 4 }} key={config.id}>
                          <Box
                            sx={{
                              p: 2,
                              border: 1,
                              borderColor: config.is_active
                                ? colorTokens.primary[500]
                                : "divider",
                              borderRadius: 1,
                              bgcolor: config.is_active
                                ? alpha(colorTokens.primary[500], 0.05)
                                : "transparent",
                            }}
                          >
                            <Typography
                              variant="subtitle2"
                              sx={{ fontWeight: config.is_active ? 600 : 400 }}
                            >
                              {config.name}
                              {config.is_active && " ✓"}
                            </Typography>
                            <Typography
                              variant="caption"
                              color="text.secondary"
                              display="block"
                            >
                              {config.mediamtx_url}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {config.use_tcp ? "TCP" : "UDP"} •
                              {config.auth_enabled
                                ? " Autenticación"
                                : " Sin auth"}{" "}
                              •{config.max_reconnects} reintentos
                            </Typography>
                          </Box>
                        </Grid>
                      ))
                    )}
                  </Grid>
                </Paper>
              )}
            </Grid>
          </Grid>
        </Box>
      </Fade>

      {/* FAB para publicar cámara */}
      <Zoom in={remote.servers.some(s => s.is_authenticated) && availableCamerasCount > 0}>
        <Tooltip 
          title={
            availableCamerasCount > 0
              ? `${availableCamerasCount} cámara${availableCamerasCount > 1 ? 's' : ''} disponible${availableCamerasCount > 1 ? 's' : ''} para publicar`
              : "No hay cámaras disponibles"
          }
          placement="left"
        >
          <Fab
            color="primary"
            sx={{
              position: 'fixed',
              bottom: 24,
              right: 24,
              boxShadow: 4,
            }}
            onClick={() => setPublishModalOpen(true)}
          >
            <Badge 
              badgeContent={availableCamerasCount} 
              color="secondary"
              max={9}
            >
              <PublishIcon />
            </Badge>
          </Fab>
        </Tooltip>
      </Zoom>

      {/* Modal de publicación */}
      <PublishCameraModal
        open={publishModalOpen}
        onClose={() => setPublishModalOpen(false)}
        onPublishSuccess={handlePublishSuccess}
      />
    </Container>
  );
});

PublishingDashboard.displayName = "PublishingDashboard";

export default PublishingDashboard;
