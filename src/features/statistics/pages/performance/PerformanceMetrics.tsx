/**
 * ⚡ Performance Metrics - Universal Camera Viewer
 * Métricas de rendimiento del sistema
 */

import React, { memo, useState, useEffect } from "react";
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  CircularProgress,
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  ToggleButton,
  ToggleButtonGroup,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  IconButton,
  Fade,
  Grow,
  Alert,
} from "@mui/material";
import {
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Timer as LatencyIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
} from "@mui/icons-material";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  ResponsiveContainer,
  Legend,
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
} from "recharts";
import { format } from "date-fns";
import { es } from "date-fns/locale";

interface PerformanceData {
  timestamp: string;
  fps: number;
  latency: number;
  cpuUsage: number;
  memoryUsage: number;
  bandwidth: number;
}

interface CameraPerformance {
  cameraId: string;
  cameraName: string;
  currentFPS: number;
  targetFPS: number;
  latency: number;
  packetLoss: number;
  uptime: number;
  status: "optimal" | "warning" | "critical";
}

const generateMockData = (): PerformanceData[] => {
  return Array.from({ length: 60 }, (_, i) => ({
    timestamp: new Date(Date.now() - (60 - i) * 60000).toISOString(),
    fps: Math.floor(Math.random() * 5) + 23,
    latency: Math.floor(Math.random() * 20) + 30,
    cpuUsage: Math.floor(Math.random() * 30) + 40,
    memoryUsage: Math.floor(Math.random() * 20) + 60,
    bandwidth: Math.floor(Math.random() * 50) + 100,
  }));
};

const mockCameraPerformance: CameraPerformance[] = [
  {
    cameraId: "cam1",
    cameraName: "Entrada Principal",
    currentFPS: 25,
    targetFPS: 30,
    latency: 42,
    packetLoss: 0.1,
    uptime: 99.9,
    status: "optimal",
  },
  {
    cameraId: "cam2",
    cameraName: "Almacén Sur",
    currentFPS: 22,
    targetFPS: 30,
    latency: 65,
    packetLoss: 2.5,
    uptime: 98.5,
    status: "warning",
  },
  {
    cameraId: "cam3",
    cameraName: "Pasillo Central",
    currentFPS: 15,
    targetFPS: 30,
    latency: 120,
    packetLoss: 5.2,
    uptime: 95.2,
    status: "critical",
  },
];

const MetricCard = memo(({ 
  title, 
  value, 
  unit, 
  icon, 
  color, 
  trend,
  info 
}: { 
  title: string; 
  value: number | string; 
  unit: string; 
  icon: React.ReactNode; 
  color: string;
  trend?: "up" | "down" | "stable";
  info?: string;
}) => {
  return (
    <Card sx={{ height: "100%" }}>
      <CardContent>
        <Box sx={{ display: "flex", alignItems: "flex-start", mb: 2 }}>
          <Box
            sx={{
              p: 1,
              borderRadius: 2,
              backgroundColor: `${color}15`,
              color: color,
              mr: 2,
            }}
          >
            {icon}
          </Box>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="body2" color="text.secondary">
              {title}
            </Typography>
          </Box>
          {info && (
            <Tooltip title={info}>
              <IconButton size="small">
                <InfoIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
        <Box sx={{ display: "flex", alignItems: "baseline", gap: 1 }}>
          <Typography variant="h4" component="div">
            {value}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {unit}
          </Typography>
          {trend && (
            <Box sx={{ ml: "auto" }}>
              {trend === "up" && <TrendingUpIcon color="success" />}
              {trend === "down" && <TrendingDownIcon color="error" />}
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
});

MetricCard.displayName = "MetricCard";

export const PerformanceMetrics = memo(() => {
  const [timeRange, setTimeRange] = useState<"1h" | "6h" | "24h">("1h");
  const [selectedCamera, setSelectedCamera] = useState<string>("all");
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>(generateMockData());
  const [loading, setLoading] = useState(false);

  const handleRefresh = async () => {
    setLoading(true);
    // TODO: Implementar llamada real a API
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setPerformanceData(generateMockData());
    setLoading(false);
  };

  // Calculate current metrics
  const currentMetrics = performanceData[performanceData.length - 1] || {
    fps: 0,
    latency: 0,
    cpuUsage: 0,
    memoryUsage: 0,
    bandwidth: 0,
  };

  const systemHealthScore = Math.round(
    (100 - currentMetrics.cpuUsage) * 0.3 +
    (100 - currentMetrics.memoryUsage) * 0.3 +
    (currentMetrics.fps / 30) * 100 * 0.4
  );

  const radialData = [
    {
      name: "Salud del Sistema",
      value: systemHealthScore,
      fill: systemHealthScore > 80 ? "#4caf50" : systemHealthScore > 60 ? "#ff9800" : "#f44336",
    },
  ];

  return (
    <Fade in timeout={600}>
      <Box>
        {/* Header */}
        <Box sx={{ display: "flex", alignItems: "center", mb: 3, gap: 2 }}>
          <Typography variant="h6" component="h2" sx={{ flexGrow: 1 }}>
            Métricas de Rendimiento
          </Typography>

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Cámara</InputLabel>
            <Select
              value={selectedCamera}
              onChange={(e) => setSelectedCamera(e.target.value)}
              label="Cámara"
            >
              <MenuItem value="all">Todas</MenuItem>
              <MenuItem value="cam1">Entrada Principal</MenuItem>
              <MenuItem value="cam2">Almacén Sur</MenuItem>
              <MenuItem value="cam3">Pasillo Central</MenuItem>
            </Select>
          </FormControl>

          <ToggleButtonGroup
            value={timeRange}
            exclusive
            onChange={(_, value) => value && setTimeRange(value)}
            size="small"
          >
            <ToggleButton value="1h">1h</ToggleButton>
            <ToggleButton value="6h">6h</ToggleButton>
            <ToggleButton value="24h">24h</ToggleButton>
          </ToggleButtonGroup>

          <Tooltip title="Actualizar">
            <IconButton onClick={handleRefresh} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>

        {loading && <LinearProgress sx={{ mb: 2 }} />}

        {/* Current Metrics */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Grow in timeout={800}>
              <Box>
                <MetricCard
                  title="FPS Promedio"
                  value={currentMetrics.fps}
                  unit="fps"
                  icon={<SpeedIcon />}
                  color="#2196f3"
                  trend={currentMetrics.fps > 24 ? "up" : "down"}
                  info="Frames por segundo promedio en todas las cámaras"
                />
              </Box>
            </Grow>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Grow in timeout={800} style={{ transitionDelay: "100ms" }}>
              <Box>
                <MetricCard
                  title="Latencia"
                  value={currentMetrics.latency}
                  unit="ms"
                  icon={<LatencyIcon />}
                  color="#ff9800"
                  trend={currentMetrics.latency < 50 ? "up" : "down"}
                  info="Latencia promedio de red"
                />
              </Box>
            </Grow>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Grow in timeout={800} style={{ transitionDelay: "200ms" }}>
              <Box>
                <MetricCard
                  title="Uso de CPU"
                  value={currentMetrics.cpuUsage}
                  unit="%"
                  icon={<MemoryIcon />}
                  color="#9c27b0"
                  trend={currentMetrics.cpuUsage < 70 ? "up" : "down"}
                  info="Porcentaje de uso del procesador"
                />
              </Box>
            </Grow>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Grow in timeout={800} style={{ transitionDelay: "300ms" }}>
              <Box>
                <MetricCard
                  title="Ancho de Banda"
                  value={currentMetrics.bandwidth}
                  unit="Mbps"
                  icon={<StorageIcon />}
                  color="#4caf50"
                  trend="stable"
                  info="Ancho de banda total utilizado"
                />
              </Box>
            </Grow>
          </Grid>
        </Grid>

        {/* Charts */}
        <Grid container spacing={3}>
          {/* System Health */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Grow in timeout={1000} style={{ transitionDelay: "400ms" }}>
              <Paper sx={{ p: 3, height: 400 }}>
                <Typography variant="h6" gutterBottom>
                  Salud del Sistema
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <RadialBarChart cx="50%" cy="50%" innerRadius="60%" outerRadius="90%" data={radialData}>
                    <PolarAngleAxis
                      type="number"
                      domain={[0, 100]}
                      angleAxisId={0}
                      tick={false}
                    />
                    <RadialBar
                      dataKey="value"
                      cornerRadius={10}
                      fill={radialData[0].fill}
                    />
                  </RadialBarChart>
                </ResponsiveContainer>
                <Box sx={{ textAlign: "center", mt: -8 }}>
                  <Typography variant="h3">{systemHealthScore}%</Typography>
                  <Chip
                    label={
                      systemHealthScore > 80
                        ? "Excelente"
                        : systemHealthScore > 60
                        ? "Bueno"
                        : "Requiere Atención"
                    }
                    color={
                      systemHealthScore > 80
                        ? "success"
                        : systemHealthScore > 60
                        ? "warning"
                        : "error"
                    }
                  />
                </Box>
              </Paper>
            </Grow>
          </Grid>

          {/* Performance Trends */}
          <Grid size={{ xs: 12, md: 8 }}>
            <Grow in timeout={1000} style={{ transitionDelay: "500ms" }}>
              <Paper sx={{ p: 3, height: 400 }}>
                <Typography variant="h6" gutterBottom>
                  Tendencias de Rendimiento
                </Typography>
                <ResponsiveContainer width="100%" height={320}>
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => format(new Date(value), "HH:mm", { locale: es })}
                    />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <ChartTooltip
                      labelFormatter={(value) =>
                        format(new Date(value), "dd/MM/yyyy HH:mm", { locale: es })
                      }
                    />
                    <Legend />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="fps"
                      stroke="#2196f3"
                      name="FPS"
                      strokeWidth={2}
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="latency"
                      stroke="#ff9800"
                      name="Latencia (ms)"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Paper>
            </Grow>
          </Grid>

          {/* Resource Usage */}
          <Grid size={12}>
            <Grow in timeout={1000} style={{ transitionDelay: "600ms" }}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Uso de Recursos
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => format(new Date(value), "HH:mm", { locale: es })}
                    />
                    <YAxis />
                    <ChartTooltip
                      labelFormatter={(value) =>
                        format(new Date(value), "dd/MM/yyyy HH:mm", { locale: es })
                      }
                    />
                    <Legend />
                    <Area
                      type="monotone"
                      dataKey="cpuUsage"
                      stackId="1"
                      stroke="#9c27b0"
                      fill="#9c27b0"
                      name="CPU %"
                    />
                    <Area
                      type="monotone"
                      dataKey="memoryUsage"
                      stackId="1"
                      stroke="#4caf50"
                      fill="#4caf50"
                      name="Memoria %"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Paper>
            </Grow>
          </Grid>

          {/* Camera Performance Table */}
          <Grid size={12}>
            <Grow in timeout={1000} style={{ transitionDelay: "700ms" }}>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Cámara</TableCell>
                      <TableCell align="center">FPS</TableCell>
                      <TableCell align="center">Latencia</TableCell>
                      <TableCell align="center">Pérdida de Paquetes</TableCell>
                      <TableCell align="center">Uptime</TableCell>
                      <TableCell align="center">Estado</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {mockCameraPerformance.map((camera) => (
                      <TableRow key={camera.cameraId}>
                        <TableCell>{camera.cameraName}</TableCell>
                        <TableCell align="center">
                          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 1 }}>
                            <Typography>{camera.currentFPS}/{camera.targetFPS}</Typography>
                            <LinearProgress
                              variant="determinate"
                              value={(camera.currentFPS / camera.targetFPS) * 100}
                              sx={{ width: 60, height: 6, borderRadius: 3 }}
                            />
                          </Box>
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={`${camera.latency}ms`}
                            size="small"
                            color={camera.latency < 50 ? "success" : camera.latency < 100 ? "warning" : "error"}
                          />
                        </TableCell>
                        <TableCell align="center">{camera.packetLoss}%</TableCell>
                        <TableCell align="center">{camera.uptime}%</TableCell>
                        <TableCell align="center">
                          <Chip
                            label={camera.status}
                            size="small"
                            color={
                              camera.status === "optimal"
                                ? "success"
                                : camera.status === "warning"
                                ? "warning"
                                : "error"
                            }
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grow>
          </Grid>
        </Grid>

        {/* Performance Alert */}
        {currentMetrics.cpuUsage > 80 && (
          <Fade in>
            <Alert severity="warning" sx={{ mt: 3 }}>
              El uso de CPU está por encima del 80%. Considera reducir la calidad de streaming o el número de cámaras activas.
            </Alert>
          </Fade>
        )}
      </Box>
    </Fade>
  );
});

PerformanceMetrics.displayName = "PerformanceMetrics";

export default PerformanceMetrics;