/**
 * 📈 Connection Analytics - Universal Camera Viewer
 * Análisis detallado de conexiones de cámaras
 */

import React, { memo, useState, useCallback } from "react";
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Card,
  CardContent,
  Chip,
  ToggleButton,
  ToggleButtonGroup,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  Fade,
  Grow,
} from "@mui/material";
import {
  Timeline as TimelineIcon,
  CalendarToday as CalendarIcon,
  BarChart as BarChartIcon,
  TableChart as TableIcon,
  Download as DownloadIcon,
  FilterList as FilterIcon,
} from "@mui/icons-material";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { format } from "date-fns";
import { es } from "date-fns/locale";

type ViewMode = "chart" | "table";
type TimeRange = "24h" | "7d" | "30d" | "90d";

interface ConnectionData {
  timestamp: string;
  successful: number;
  failed: number;
  avgDuration: number;
  avgLatency: number;
}

interface ConnectionLog {
  id: string;
  cameraName: string;
  ip: string;
  startTime: string;
  duration: number;
  status: "success" | "failed" | "timeout";
  bytesTransferred: number;
  avgFPS: number;
  errorMessage?: string;
}

// Mock data generation
const generateMockData = (range: TimeRange): ConnectionData[] => {
  const points = range === "24h" ? 24 : range === "7d" ? 7 : range === "30d" ? 30 : 90;
  return Array.from({ length: points }, (_, i) => ({
    timestamp: new Date(Date.now() - (points - i) * 3600000).toISOString(),
    successful: Math.floor(Math.random() * 50) + 150,
    failed: Math.floor(Math.random() * 10) + 5,
    avgDuration: Math.floor(Math.random() * 30) + 20,
    avgLatency: Math.floor(Math.random() * 20) + 30,
  }));
};

const mockLogs: ConnectionLog[] = [
  {
    id: "1",
    cameraName: "Entrada Principal",
    ip: "192.168.1.100",
    startTime: new Date().toISOString(),
    duration: 3600,
    status: "success",
    bytesTransferred: 125000000,
    avgFPS: 25,
  },
  {
    id: "2",
    cameraName: "Almacén Sur",
    ip: "192.168.1.101",
    startTime: new Date(Date.now() - 3600000).toISOString(),
    duration: 1800,
    status: "failed",
    bytesTransferred: 0,
    avgFPS: 0,
    errorMessage: "Connection timeout",
  },
  // Add more mock logs...
];

export const ConnectionAnalytics = memo(() => {
  const [viewMode, setViewMode] = useState<ViewMode>("chart");
  const [timeRange, setTimeRange] = useState<TimeRange>("24h");
  const [selectedCamera, setSelectedCamera] = useState<string>("all");
  const [data, setData] = useState<ConnectionData[]>(generateMockData("24h"));

  const handleTimeRangeChange = useCallback((newRange: TimeRange) => {
    setTimeRange(newRange);
    setData(generateMockData(newRange));
  }, []);

  const formatXAxis = (tickItem: string) => {
    const date = new Date(tickItem);
    if (timeRange === "24h") {
      return format(date, "HH:mm", { locale: es });
    } else if (timeRange === "7d") {
      return format(date, "EEE", { locale: es });
    } else {
      return format(date, "dd/MM", { locale: es });
    }
  };

  const totalConnections = data.reduce((acc, d) => acc + d.successful + d.failed, 0);
  const successRate = Math.round(
    (data.reduce((acc, d) => acc + d.successful, 0) / totalConnections) * 100
  );
  const avgLatency = Math.round(
    data.reduce((acc, d) => acc + d.avgLatency, 0) / data.length
  );

  return (
    <Fade in timeout={600}>
      <Box>
        {/* Header Controls */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            mb: 3,
            flexWrap: "wrap",
            gap: 2,
          }}
        >
          <Typography variant="h6" component="h2">
            Análisis de Conexiones
          </Typography>

          <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
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
              onChange={(_, value) => value && handleTimeRangeChange(value)}
              size="small"
            >
              <ToggleButton value="24h">24h</ToggleButton>
              <ToggleButton value="7d">7d</ToggleButton>
              <ToggleButton value="30d">30d</ToggleButton>
              <ToggleButton value="90d">90d</ToggleButton>
            </ToggleButtonGroup>

            <ToggleButtonGroup
              value={viewMode}
              exclusive
              onChange={(_, value) => value && setViewMode(value)}
              size="small"
            >
              <ToggleButton value="chart">
                <BarChartIcon />
              </ToggleButton>
              <ToggleButton value="table">
                <TableIcon />
              </ToggleButton>
            </ToggleButtonGroup>

            <Tooltip title="Exportar datos">
              <IconButton>
                <DownloadIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Summary Cards */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Grow in timeout={800}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Total Conexiones
                  </Typography>
                  <Typography variant="h4">{totalConnections}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    en {timeRange}
                  </Typography>
                </CardContent>
              </Card>
            </Grow>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Grow in timeout={800} style={{ transitionDelay: "100ms" }}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Tasa de Éxito
                  </Typography>
                  <Typography variant="h4" color="success.main">
                    {successRate}%
                  </Typography>
                  <Chip
                    label={successRate > 95 ? "Excelente" : "Normal"}
                    size="small"
                    color={successRate > 95 ? "success" : "default"}
                  />
                </CardContent>
              </Card>
            </Grow>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Grow in timeout={800} style={{ transitionDelay: "200ms" }}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Latencia Promedio
                  </Typography>
                  <Typography variant="h4">{avgLatency}ms</Typography>
                  <Chip
                    label={avgLatency < 50 ? "Óptima" : "Mejorable"}
                    size="small"
                    color={avgLatency < 50 ? "success" : "warning"}
                  />
                </CardContent>
              </Card>
            </Grow>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Grow in timeout={800} style={{ transitionDelay: "300ms" }}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Duración Promedio
                  </Typography>
                  <Typography variant="h4">
                    {Math.round(data.reduce((acc, d) => acc + d.avgDuration, 0) / data.length)}s
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    por sesión
                  </Typography>
                </CardContent>
              </Card>
            </Grow>
          </Grid>
        </Grid>

        {/* Main Content */}
        {viewMode === "chart" ? (
          <Grow in timeout={1000}>
            <Paper sx={{ p: 3 }}>
              {/* Connection Trends */}
              <Typography variant="h6" gutterBottom>
                Tendencia de Conexiones
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" tickFormatter={formatXAxis} />
                  <YAxis />
                  <ChartTooltip
                    labelFormatter={(value) =>
                      format(new Date(value), "dd/MM/yyyy HH:mm", { locale: es })
                    }
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="successful"
                    stackId="1"
                    stroke="#4caf50"
                    fill="#4caf50"
                    name="Exitosas"
                  />
                  <Area
                    type="monotone"
                    dataKey="failed"
                    stackId="1"
                    stroke="#f44336"
                    fill="#f44336"
                    name="Fallidas"
                  />
                </AreaChart>
              </ResponsiveContainer>

              {/* Latency Trends */}
              <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>
                Latencia y Duración
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" tickFormatter={formatXAxis} />
                  <YAxis yAxisId="left" orientation="left" />
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
                    dataKey="avgLatency"
                    stroke="#2196f3"
                    name="Latencia (ms)"
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="avgDuration"
                    stroke="#ff9800"
                    name="Duración (s)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </Paper>
          </Grow>
        ) : (
          <Grow in timeout={1000}>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Cámara</TableCell>
                    <TableCell>IP</TableCell>
                    <TableCell>Inicio</TableCell>
                    <TableCell>Duración</TableCell>
                    <TableCell>Estado</TableCell>
                    <TableCell>Datos</TableCell>
                    <TableCell>FPS</TableCell>
                    <TableCell>Error</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {mockLogs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell>{log.cameraName}</TableCell>
                      <TableCell>{log.ip}</TableCell>
                      <TableCell>
                        {format(new Date(log.startTime), "dd/MM HH:mm", { locale: es })}
                      </TableCell>
                      <TableCell>{Math.floor(log.duration / 60)}m</TableCell>
                      <TableCell>
                        <Chip
                          label={log.status}
                          size="small"
                          color={
                            log.status === "success"
                              ? "success"
                              : log.status === "failed"
                              ? "error"
                              : "warning"
                          }
                        />
                      </TableCell>
                      <TableCell>
                        {(log.bytesTransferred / 1024 / 1024).toFixed(1)} MB
                      </TableCell>
                      <TableCell>{log.avgFPS}</TableCell>
                      <TableCell>{log.errorMessage || "-"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Grow>
        )}
      </Box>
    </Fade>
  );
});

ConnectionAnalytics.displayName = "ConnectionAnalytics";

export default ConnectionAnalytics;