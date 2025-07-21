/**
 * 🚦 Health Status Card Component - Universal Camera Viewer
 * Semáforo de salud del sistema con información detallada
 */

import React, { memo } from "react";
import {
  Card,
  CardContent,
  Box,
  Typography,
  Tooltip,
  IconButton,
  LinearProgress,
  Chip,
} from "@mui/material";
import {
  CheckCircle as HealthyIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from "@mui/icons-material";
import { PublishingHealth } from "../../types";

interface HealthStatusCardProps {
  health: PublishingHealth | null;
  isLoading?: boolean;
  onInfoClick?: () => void;
}

/**
 * Componente de card de salud del sistema
 */
export const HealthStatusCard = memo<HealthStatusCardProps>(
  ({ health, isLoading = false, onInfoClick }) => {
    const getStatusIcon = () => {
      if (!health) return null;

      switch (health.overall_status) {
        case "healthy":
          return <HealthyIcon sx={{ fontSize: 48, color: "#4caf50" }} />;
        case "warning":
          return <WarningIcon sx={{ fontSize: 48, color: "#ff9800" }} />;
        case "error":
          return <ErrorIcon sx={{ fontSize: 48, color: "#f44336" }} />;
      }
    };

    const getStatusColor = () => {
      if (!health) return "grey.400";

      switch (health.overall_status) {
        case "healthy":
          return "#4caf50";
        case "warning":
          return "#ff9800";
        case "error":
          return "#f44336";
      }
    };

    const getStatusLabel = () => {
      if (!health) return "Sin datos";

      switch (health.overall_status) {
        case "healthy":
          return "Sistema Saludable";
        case "warning":
          return "Advertencias Activas";
        case "error":
          return "Errores Detectados";
      }
    };

    const getHealthPercentage = () => {
      if (!health || health.total_servers === 0) return 0;
      return (health.healthy_servers / health.total_servers) * 100;
    };

    return (
      <Card sx={{ height: "100%" }}>
        <CardContent>
          <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
            <Typography variant="h6" sx={{ flex: 1 }}>
              Estado del Sistema
            </Typography>
            {onInfoClick && (
              <Tooltip title="Ver detalles">
                <IconButton size="small" onClick={onInfoClick}>
                  <InfoIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>

          {isLoading ? (
            <Box sx={{ py: 4 }}>
              <LinearProgress />
            </Box>
          ) : health ? (
            <Box>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  mb: 3,
                }}
              >
                {(() => {
                  const icon = getStatusIcon();
                  return icon ? (
                    <Tooltip title={getStatusLabel()}>{icon}</Tooltip>
                  ) : null;
                })()}
              </Box>

              <Typography
                variant="h5"
                align="center"
                sx={{ color: getStatusColor(), mb: 3 }}
              >
                {getStatusLabel()}
              </Typography>

              <Box sx={{ mb: 2 }}>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    mb: 1,
                  }}
                >
                  <Typography variant="body2" color="text.secondary">
                    Servidores activos
                  </Typography>
                  <Typography variant="body2">
                    {health.healthy_servers} / {health.total_servers}
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={getHealthPercentage()}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: "grey.300",
                    "& .MuiLinearProgress-bar": {
                      backgroundColor: getStatusColor(),
                    },
                  }}
                />
              </Box>

              {health.active_alerts.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    gutterBottom
                  >
                    Alertas activas
                  </Typography>
                  <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                    {health.active_alerts.slice(0, 3).map((alert, index) => (
                      <Chip
                        key={index}
                        label={alert.alert_type}
                        size="small"
                        color={
                          alert.severity === "critical" ? "error" : "warning"
                        }
                      />
                    ))}
                    {health.active_alerts.length > 3 && (
                      <Chip
                        label={`+${health.active_alerts.length - 3} más`}
                        size="small"
                        variant="outlined"
                      />
                    )}
                  </Box>
                </Box>
              )}
            </Box>
          ) : (
            <Box sx={{ py: 4, textAlign: "center" }}>
              <Typography variant="body2" color="text.secondary">
                Sin datos de salud disponibles
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    );
  }
);

HealthStatusCard.displayName = "HealthStatusCard";
