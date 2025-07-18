/**
 * 🌐 Network Scan History - Universal Camera Viewer
 * Historial de escaneos de red
 */

import React, { memo, useState, useCallback } from "react";
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Button,
  LinearProgress,
  Collapse,
  Card,
  CardContent,
  Grid,
  Tooltip,
  Menu,
  MenuItem,
  TextField,
  InputAdornment,
  Fade,
  Grow,
} from "@mui/material";
import {
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  NetworkCheck as ScanIcon,
  MoreVert as MoreIcon,
  Search as SearchIcon,
  Download as ExportIcon,
  Delete as DeleteIcon,
  Replay as RescanIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from "@mui/icons-material";
import { format } from "date-fns";
import { es } from "date-fns/locale";

interface NetworkScan {
  scanId: string;
  scanType: "quick" | "deep" | "custom" | "single";
  scanName?: string;
  targetNetwork: string;
  startTime: string;
  endTime?: string;
  duration?: number;
  totalHosts: number;
  hostsAlive: number;
  camerasFound: number;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  progress?: number;
  createdBy: string;
}

interface ScanResult {
  ip: string;
  mac?: string;
  hostname?: string;
  isCamera: boolean;
  brand?: string;
  model?: string;
  openPorts: number[];
  services: string[];
  responseTime: number;
}

const mockScans: NetworkScan[] = [
  {
    scanId: "1",
    scanType: "deep",
    scanName: "Escaneo completo de red",
    targetNetwork: "192.168.1.0/24",
    startTime: new Date().toISOString(),
    endTime: new Date(Date.now() + 1800000).toISOString(),
    duration: 1800,
    totalHosts: 254,
    hostsAlive: 42,
    camerasFound: 8,
    status: "completed",
    createdBy: "admin",
  },
  {
    scanId: "2",
    scanType: "quick",
    targetNetwork: "192.168.1.100-150",
    startTime: new Date(Date.now() - 3600000).toISOString(),
    totalHosts: 50,
    hostsAlive: 0,
    camerasFound: 0,
    status: "running",
    progress: 65,
    createdBy: "user1",
  },
  {
    scanId: "3",
    scanType: "single",
    targetNetwork: "192.168.1.200",
    startTime: new Date(Date.now() - 7200000).toISOString(),
    endTime: new Date(Date.now() - 7100000).toISOString(),
    duration: 100,
    totalHosts: 1,
    hostsAlive: 1,
    camerasFound: 1,
    status: "completed",
    createdBy: "admin",
  },
];

const mockResults: Record<string, ScanResult[]> = {
  "1": [
    {
      ip: "192.168.1.100",
      mac: "AA:BB:CC:DD:EE:FF",
      hostname: "camera-entrada",
      isCamera: true,
      brand: "Dahua",
      model: "IPC-HDW1200SP",
      openPorts: [80, 554, 8000],
      services: ["HTTP", "RTSP", "ONVIF"],
      responseTime: 12,
    },
    {
      ip: "192.168.1.101",
      isCamera: true,
      brand: "TP-Link",
      openPorts: [2020, 554],
      services: ["ONVIF", "RTSP"],
      responseTime: 25,
    },
  ],
  "3": [
    {
      ip: "192.168.1.200",
      isCamera: true,
      brand: "Hikvision",
      openPorts: [80, 554],
      services: ["HTTP", "RTSP"],
      responseTime: 8,
    },
  ],
};

const ScanStatusChip = memo(({ status }: { status: NetworkScan["status"] }) => {
  const config = {
    pending: { label: "Pendiente", color: "default" as const, icon: <WarningIcon /> },
    running: { label: "En Progreso", color: "info" as const, icon: <ScanIcon /> },
    completed: { label: "Completado", color: "success" as const, icon: <SuccessIcon /> },
    failed: { label: "Fallido", color: "error" as const, icon: <ErrorIcon /> },
    cancelled: { label: "Cancelado", color: "warning" as const, icon: <WarningIcon /> },
  };

  const { label, color, icon } = config[status];

  return <Chip label={label} color={color} size="small" icon={icon} />;
});

ScanStatusChip.displayName = "ScanStatusChip";

export const NetworkScanHistory = memo(() => {
  const [scans, setScans] = useState<NetworkScan[]>(mockScans);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState("");
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedScan, setSelectedScan] = useState<string | null>(null);

  const handleExpandRow = useCallback((scanId: string) => {
    setExpandedRow((prev) => (prev === scanId ? null : scanId));
  }, []);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, scanId: string) => {
    setAnchorEl(event.currentTarget);
    setSelectedScan(scanId);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedScan(null);
  };

  const handleRescan = (scanId: string) => {
    // TODO: Implementar reescaneo
    console.log("Rescan:", scanId);
    handleMenuClose();
  };

  const handleExport = (scanId: string) => {
    // TODO: Implementar exportación
    console.log("Export:", scanId);
    handleMenuClose();
  };

  const handleDelete = (scanId: string) => {
    setScans((prev) => prev.filter((scan) => scan.scanId !== scanId));
    handleMenuClose();
  };

  const filteredScans = scans.filter(
    (scan) =>
      scan.targetNetwork.includes(searchTerm) ||
      scan.scanName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      scan.createdBy.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalStats = {
    totalScans: scans.length,
    completedScans: scans.filter((s) => s.status === "completed").length,
    totalCameras: scans.reduce((acc, s) => acc + s.camerasFound, 0),
    totalHosts: scans.reduce((acc, s) => acc + s.hostsAlive, 0),
  };

  return (
    <Fade in timeout={600}>
      <Box>
        {/* Header */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" component="h2" gutterBottom>
            Historial de Escaneos de Red
          </Typography>

          {/* Stats Cards */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Grow in timeout={800}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Total Escaneos
                    </Typography>
                    <Typography variant="h4">{totalStats.totalScans}</Typography>
                  </CardContent>
                </Card>
              </Grow>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Grow in timeout={800} style={{ transitionDelay: "100ms" }}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Completados
                    </Typography>
                    <Typography variant="h4" color="success.main">
                      {totalStats.completedScans}
                    </Typography>
                  </CardContent>
                </Card>
              </Grow>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Grow in timeout={800} style={{ transitionDelay: "200ms" }}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Cámaras Encontradas
                    </Typography>
                    <Typography variant="h4" color="primary.main">
                      {totalStats.totalCameras}
                    </Typography>
                  </CardContent>
                </Card>
              </Grow>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Grow in timeout={800} style={{ transitionDelay: "300ms" }}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Hosts Activos
                    </Typography>
                    <Typography variant="h4">{totalStats.totalHosts}</Typography>
                  </CardContent>
                </Card>
              </Grow>
            </Grid>
          </Grid>

          {/* Search */}
          <TextField
            fullWidth
            placeholder="Buscar por red, nombre o usuario..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ mb: 2 }}
          />
        </Box>

        {/* Scans Table */}
        <Grow in timeout={1000}>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell width={40} />
                  <TableCell>Red Objetivo</TableCell>
                  <TableCell>Tipo</TableCell>
                  <TableCell>Inicio</TableCell>
                  <TableCell>Duración</TableCell>
                  <TableCell align="center">Hosts</TableCell>
                  <TableCell align="center">Cámaras</TableCell>
                  <TableCell>Estado</TableCell>
                  <TableCell>Usuario</TableCell>
                  <TableCell width={40} />
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredScans
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((scan) => (
                    <React.Fragment key={scan.scanId}>
                      <TableRow hover>
                        <TableCell>
                          <IconButton
                            size="small"
                            onClick={() => handleExpandRow(scan.scanId)}
                          >
                            {expandedRow === scan.scanId ? <CollapseIcon /> : <ExpandIcon />}
                          </IconButton>
                        </TableCell>
                        <TableCell>
                          <Box>
                            <Typography variant="body2">{scan.targetNetwork}</Typography>
                            {scan.scanName && (
                              <Typography variant="caption" color="text.secondary">
                                {scan.scanName}
                              </Typography>
                            )}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip label={scan.scanType} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell>
                          {format(new Date(scan.startTime), "dd/MM/yyyy HH:mm", { locale: es })}
                        </TableCell>
                        <TableCell>
                          {scan.duration
                            ? `${Math.floor(scan.duration / 60)}m ${scan.duration % 60}s`
                            : "-"}
                        </TableCell>
                        <TableCell align="center">
                          <Box>
                            <Typography variant="body2">
                              {scan.hostsAlive}/{scan.totalHosts}
                            </Typography>
                            <LinearProgress
                              variant="determinate"
                              value={(scan.hostsAlive / scan.totalHosts) * 100}
                              sx={{ mt: 0.5, height: 4, borderRadius: 2 }}
                            />
                          </Box>
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={scan.camerasFound}
                            size="small"
                            color={scan.camerasFound > 0 ? "primary" : "default"}
                          />
                        </TableCell>
                        <TableCell>
                          <Box>
                            <ScanStatusChip status={scan.status} />
                            {scan.status === "running" && scan.progress && (
                              <LinearProgress
                                variant="determinate"
                                value={scan.progress}
                                sx={{ mt: 1, height: 4, borderRadius: 2 }}
                              />
                            )}
                          </Box>
                        </TableCell>
                        <TableCell>{scan.createdBy}</TableCell>
                        <TableCell>
                          <IconButton
                            size="small"
                            onClick={(e) => handleMenuOpen(e, scan.scanId)}
                          >
                            <MoreIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell colSpan={10} sx={{ py: 0 }}>
                          <Collapse in={expandedRow === scan.scanId} timeout="auto" unmountOnExit>
                            <Box sx={{ p: 3 }}>
                              <Typography variant="subtitle2" gutterBottom>
                                Resultados del Escaneo
                              </Typography>
                              {mockResults[scan.scanId] ? (
                                <Table size="small">
                                  <TableHead>
                                    <TableRow>
                                      <TableCell>IP</TableCell>
                                      <TableCell>MAC</TableCell>
                                      <TableCell>Hostname</TableCell>
                                      <TableCell>Marca/Modelo</TableCell>
                                      <TableCell>Puertos</TableCell>
                                      <TableCell>Servicios</TableCell>
                                      <TableCell>Tiempo de Respuesta</TableCell>
                                    </TableRow>
                                  </TableHead>
                                  <TableBody>
                                    {mockResults[scan.scanId].map((result, index) => (
                                      <TableRow key={index}>
                                        <TableCell>{result.ip}</TableCell>
                                        <TableCell>{result.mac || "-"}</TableCell>
                                        <TableCell>{result.hostname || "-"}</TableCell>
                                        <TableCell>
                                          {result.brand ? `${result.brand} ${result.model || ""}` : "-"}
                                        </TableCell>
                                        <TableCell>{result.openPorts.join(", ")}</TableCell>
                                        <TableCell>
                                          <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
                                            {result.services.map((service) => (
                                              <Chip
                                                key={service}
                                                label={service}
                                                size="small"
                                                variant="outlined"
                                              />
                                            ))}
                                          </Box>
                                        </TableCell>
                                        <TableCell>{result.responseTime}ms</TableCell>
                                      </TableRow>
                                    ))}
                                  </TableBody>
                                </Table>
                              ) : (
                                <Typography variant="body2" color="text.secondary">
                                  No hay resultados disponibles
                                </Typography>
                              )}
                            </Box>
                          </Collapse>
                        </TableCell>
                      </TableRow>
                    </React.Fragment>
                  ))}
              </TableBody>
            </Table>
            <TablePagination
              rowsPerPageOptions={[5, 10, 25]}
              component="div"
              count={filteredScans.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={(_, newPage) => setPage(newPage)}
              onRowsPerPageChange={(e) => {
                setRowsPerPage(parseInt(e.target.value, 10));
                setPage(0);
              }}
              labelRowsPerPage="Filas por página"
            />
          </TableContainer>
        </Grow>

        {/* Context Menu */}
        <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
          <MenuItem onClick={() => selectedScan && handleRescan(selectedScan)}>
            <RescanIcon sx={{ mr: 1 }} /> Reescanear
          </MenuItem>
          <MenuItem onClick={() => selectedScan && handleExport(selectedScan)}>
            <ExportIcon sx={{ mr: 1 }} /> Exportar
          </MenuItem>
          <MenuItem onClick={() => selectedScan && handleDelete(selectedScan)} sx={{ color: "error.main" }}>
            <DeleteIcon sx={{ mr: 1 }} /> Eliminar
          </MenuItem>
        </Menu>

        {/* New Scan Button */}
        <Box sx={{ position: "fixed", bottom: 24, right: 24 }}>
          <Tooltip title="Nuevo Escaneo">
            <Button variant="contained" color="primary" startIcon={<ScanIcon />}>
              Nuevo Escaneo
            </Button>
          </Tooltip>
        </Box>
      </Box>
    </Fade>
  );
});

NetworkScanHistory.displayName = "NetworkScanHistory";

export default NetworkScanHistory;