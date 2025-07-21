/**
 * 📊 Publishing Dashboard - Universal Camera Viewer
 * Panel principal de control para publicaciones MediaMTX
 */

import React, { useEffect, memo } from "react";
import {
  Box,
  Container,
  Typography,
  Grid,
  Paper,
  Fade,
  CircularProgress,
  useTheme,
  alpha,
  Tooltip,
} from "@mui/material";
import {
  HelpOutline as HelpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
} from "@mui/icons-material";
import { usePublishingHealth } from "../hooks/usePublishingHealth";
import { usePublishingStore } from "../../../stores/publishingStore";
import { colorTokens } from "../../../design-system/tokens";

/**
 * Dashboard principal de publicación MediaMTX
 */
const PublishingDashboard = memo(() => {
  const theme = useTheme();
  const {
    systemHealth,
    publicationCounts,
    healthIndicators,
    alerts,
    isLoading,
    refresh,
  } = usePublishingHealth({
    autoRefresh: true,
    refreshInterval: 30,
  });

  const { configurations, fetchConfigurations } = usePublishingStore();

  // Cargar configuraciones al montar
  useEffect(() => {
    fetchConfigurations();
  }, [fetchConfigurations]);

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
          {/* Header */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h4" gutterBottom>
              Dashboard de Publicación
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Panel de control MediaMTX - Estado general del sistema
            </Typography>
          </Box>

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
                  {publicationCounts.running}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {publicationCounts.starting > 0 &&
                    `${publicationCounts.starting} iniciando • `}
                  {publicationCounts.error > 0 &&
                    `${publicationCounts.error} con error`}
                  {publicationCounts.starting === 0 &&
                    publicationCounts.error === 0 &&
                    "Todas funcionando correctamente"}
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
                  {systemHealth?.total_viewers || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Conectados ahora mismo
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

            {/* Resumen de Configuraciones */}
            <Grid size={12}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Configuraciones MediaMTX
                </Typography>
                <Grid container spacing={2}>
                  {configurations.length === 0 ? (
                    <Grid size={12}>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        align="center"
                      >
                        No hay configuraciones de servidor disponibles
                      </Typography>
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
            </Grid>
          </Grid>
        </Box>
      </Fade>
    </Container>
  );
});

PublishingDashboard.displayName = "PublishingDashboard";

export default PublishingDashboard;
