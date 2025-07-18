/**
 * 📊 Overview Dashboard - Universal Camera Viewer
 * Panel general de estadísticas del sistema
 */

import React, { memo, useState, useEffect } from "react";
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
  Fade,
  Grow,
  useTheme,
} from "@mui/material";
import {
  Videocam as CameraIcon,
  Link as ConnectionIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
  Speed as SpeedIcon,
  Storage as StorageIcon,
  Timer as UptimeIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
} from "@mui/icons-material";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as ChartTooltip } from "recharts";

interface SystemStats {
  totalCameras: number;
  activeCameras: number;
  totalConnections: number;
  successfulConnections: number;
  failedConnections: number;
  averageFPS: number;
  averageLatency: number;
  totalUptime: number;
  totalDataTransferred: number;
  lastUpdate: string;
}

interface QuickStat {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  trend?: "up" | "down" | "stable";
  trendValue?: string;
}

const MOCK_STATS: SystemStats = {
  totalCameras: 12,
  activeCameras: 8,
  totalConnections: 1543,
  successfulConnections: 1421,
  failedConnections: 122,
  averageFPS: 24.5,
  averageLatency: 45,
  totalUptime: 168, // hours
  totalDataTransferred: 2560, // MB
  lastUpdate: new Date().toISOString(),
};

const StatCard = memo(({ stat }: { stat: QuickStat }) => {
  const theme = useTheme();

  return (
    <Grow in timeout={800}>
      <Card
        sx={{
          height: "100%",
          position: "relative",
          overflow: "visible",
          transition: "transform 0.2s",
          "&:hover": {
            transform: "translateY(-2px)",
            boxShadow: theme.shadows[4],
          },
        }}
      >
        <CardContent>
          <Box sx={{ display: "flex", alignItems: "flex-start", mb: 2 }}>
            <Box
              sx={{
                p: 1,
                borderRadius: 2,
                backgroundColor: `${stat.color}15`,
                color: stat.color,
                mr: 2,
              }}
            >
              {stat.icon}
            </Box>
            {stat.trend && (
              <Box sx={{ ml: "auto" }}>
                {stat.trend === "up" && (
                  <Chip
                    icon={<TrendingUpIcon />}
                    label={stat.trendValue}
                    size="small"
                    color="success"
                    variant="outlined"
                  />
                )}
                {stat.trend === "down" && (
                  <Chip
                    icon={<TrendingDownIcon />}
                    label={stat.trendValue}
                    size="small"
                    color="error"
                    variant="outlined"
                  />
                )}
              </Box>
            )}
          </Box>
          <Typography variant="h4" component="div" sx={{ mb: 1 }}>
            {stat.value}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {stat.label}
          </Typography>
        </CardContent>
      </Card>
    </Grow>
  );
});

StatCard.displayName = "StatCard";

export const OverviewDashboard = memo(() => {
  const theme = useTheme();
  const [stats, setStats] = useState<SystemStats>(MOCK_STATS);
  const [loading, setLoading] = useState(false);

  const handleRefresh = async () => {
    setLoading(true);
    // TODO: Implementar llamada real a API
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setStats({
      ...MOCK_STATS,
      lastUpdate: new Date().toISOString(),
    });
    setLoading(false);
  };

  const successRate = Math.round(
    (stats.successfulConnections / stats.totalConnections) * 100
  );

  const pieData = [
    { name: "Exitosas", value: stats.successfulConnections, color: theme.palette.success.main },
    { name: "Fallidas", value: stats.failedConnections, color: theme.palette.error.main },
  ];

  const quickStats: QuickStat[] = [
    {
      label: "Cámaras Activas",
      value: `${stats.activeCameras}/${stats.totalCameras}`,
      icon: <CameraIcon />,
      color: theme.palette.primary.main,
      trend: "up",
      trendValue: "+2",
    },
    {
      label: "Tasa de Éxito",
      value: `${successRate}%`,
      icon: <SuccessIcon />,
      color: theme.palette.success.main,
      trend: successRate > 90 ? "up" : "down",
      trendValue: successRate > 90 ? "+3%" : "-2%",
    },
    {
      label: "FPS Promedio",
      value: stats.averageFPS.toFixed(1),
      icon: <SpeedIcon />,
      color: theme.palette.info.main,
      trend: "stable",
    },
    {
      label: "Latencia",
      value: `${stats.averageLatency}ms`,
      icon: <ConnectionIcon />,
      color: theme.palette.warning.main,
      trend: stats.averageLatency < 50 ? "up" : "down",
      trendValue: stats.averageLatency < 50 ? "-5ms" : "+8ms",
    },
  ];

  return (
    <Fade in timeout={600}>
      <Box>
        {/* Header with refresh */}
        <Box sx={{ display: "flex", alignItems: "center", mb: 3 }}>
          <Typography variant="h6" component="h2" sx={{ flexGrow: 1 }}>
            Resumen General
          </Typography>
          <Tooltip title="Actualizar estadísticas">
            <IconButton onClick={handleRefresh} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>

        {loading && <LinearProgress sx={{ mb: 2 }} />}

        {/* Quick Stats Grid */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {quickStats.map((stat, index) => (
            <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
              <StatCard stat={stat} />
            </Grid>
          ))}
        </Grid>

        {/* Detailed Stats */}
        <Grid container spacing={3}>
          {/* Connection Success Chart */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Grow in timeout={1000} style={{ transitionDelay: "200ms" }}>
              <Paper sx={{ p: 3, height: 350 }}>
                <Typography variant="h6" gutterBottom>
                  Distribución de Conexiones
                </Typography>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <ChartTooltip />
                  </PieChart>
                </ResponsiveContainer>
                <Box sx={{ textAlign: "center", mt: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Total de conexiones: {stats.totalConnections}
                  </Typography>
                </Box>
              </Paper>
            </Grow>
          </Grid>

          {/* System Info */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Grow in timeout={1000} style={{ transitionDelay: "300ms" }}>
              <Paper sx={{ p: 3, height: 350 }}>
                <Typography variant="h6" gutterBottom>
                  Información del Sistema
                </Typography>
                <Box sx={{ mt: 3 }}>
                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                      <UptimeIcon sx={{ mr: 1, color: "text.secondary" }} />
                      <Typography variant="body2" color="text.secondary">
                        Tiempo Total de Actividad
                      </Typography>
                    </Box>
                    <Typography variant="h5">
                      {Math.floor(stats.totalUptime / 24)}d {stats.totalUptime % 24}h
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                      <StorageIcon sx={{ mr: 1, color: "text.secondary" }} />
                      <Typography variant="body2" color="text.secondary">
                        Datos Transferidos
                      </Typography>
                    </Box>
                    <Typography variant="h5">
                      {(stats.totalDataTransferred / 1024).toFixed(1)} GB
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Última actualización:{" "}
                      {new Date(stats.lastUpdate).toLocaleTimeString()}
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            </Grow>
          </Grid>

          {/* Top Cameras by Activity */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Grow in timeout={1000} style={{ transitionDelay: "400ms" }}>
              <Paper sx={{ p: 3, height: 350 }}>
                <Typography variant="h6" gutterBottom>
                  Cámaras Más Activas
                </Typography>
                <Box sx={{ mt: 2 }}>
                  {[
                    { name: "Entrada Principal", connections: 245, status: "online" },
                    { name: "Almacén Sur", connections: 198, status: "online" },
                    { name: "Pasillo Central", connections: 156, status: "offline" },
                    { name: "Estacionamiento", connections: 134, status: "online" },
                  ].map((camera, index) => (
                    <Box
                      key={index}
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        mb: 2,
                        p: 1.5,
                        borderRadius: 1,
                        backgroundColor: "action.hover",
                      }}
                    >
                      <CameraIcon sx={{ mr: 2, color: "text.secondary" }} />
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="body2">{camera.name}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {camera.connections} conexiones
                        </Typography>
                      </Box>
                      <Chip
                        label={camera.status}
                        size="small"
                        color={camera.status === "online" ? "success" : "default"}
                        variant="outlined"
                      />
                    </Box>
                  ))}
                </Box>
              </Paper>
            </Grow>
          </Grid>
        </Grid>
      </Box>
    </Fade>
  );
});

OverviewDashboard.displayName = "OverviewDashboard";

export default OverviewDashboard;