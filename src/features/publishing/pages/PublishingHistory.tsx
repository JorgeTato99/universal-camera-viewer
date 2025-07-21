/**
 * 📜 Publishing History Page - Universal Camera Viewer
 * Historial de sesiones de publicación
 */

import React, { useState, useEffect, memo } from "react";
import {
  Box,
  Container,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Fade,
} from "@mui/material";
import {
  FilterList as FilterIcon,
  Info as InfoIcon,
  DeleteSweep as CleanupIcon,
  GetApp as ExportIcon,
} from "@mui/icons-material";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import { es } from "date-fns/locale";
import { publishingService } from "../../../services/publishing";
import { useCameraStoreV2 } from "../../../stores/cameraStore.v2";
import { useNotificationStore } from "../../../stores/notificationStore";
import { PublishingHistorySession, HistoryFilters } from "../types";
import {
  formatDate,
  formatDuration,
  formatBytes,
  formatBitrate,
} from "../utils";

/**
 * Página de historial de publicaciones
 */
const PublishingHistory = memo(() => {
  const { cameras, loadCameras } = useCameraStoreV2();
  const { showError, showSuccess } = useNotificationStore();

  const [sessions, setSessions] = useState<PublishingHistorySession[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedSession, setSelectedSession] =
    useState<PublishingHistorySession | null>(null);
  const [cleanupDialogOpen, setCleanupDialogOpen] = useState(false);

  // Filtros
  const [filters, setFilters] = useState<HistoryFilters>({
    page: 1,
    page_size: 10,
    order_by: "start_time",
    order_desc: true,
  });

  // Cargar cámaras al montar
  useEffect(() => {
    loadCameras();
  }, [loadCameras]);

  // Cargar historial
  useEffect(() => {
    loadHistory();
  }, [filters]);

  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const response = await publishingService.getHistory(filters);
      if (response.success && response.data) {
        setSessions(response.data.items);
        setTotalCount(response.data.total);
      }
    } catch (error) {
      showError("Error", "Error al cargar el historial");
    } finally {
      setIsLoading(false);
    }
  };

  const handleChangePage = (_: unknown, newPage: number) => {
    setFilters((prev) => ({ ...prev, page: newPage + 1 }));
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFilters((prev) => ({
      ...prev,
      page_size: parseInt(event.target.value, 10),
      page: 1,
    }));
  };

  const handleCleanup = async (daysOld: number, keepErrors: boolean) => {
    try {
      const response = await publishingService.cleanupHistory(
        daysOld,
        keepErrors,
        false
      );
      if (response.success && response.data) {
        showSuccess("Éxito", `Se eliminaron ${response.data.deleted_count} sesiones antiguas`);
        loadHistory();
      }
    } catch (error) {
      showError("Error", "Error al limpiar el historial");
    }
    setCleanupDialogOpen(false);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "success";
      case "error":
        return "error";
      case "stopped":
        return "warning";
      default:
        return "default";
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
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
                Historial de Publicaciones
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Registro histórico de todas las sesiones de publicación
              </Typography>
            </Box>
            <Box sx={{ display: "flex", gap: 2 }}>
              <Button
                variant="outlined"
                startIcon={<CleanupIcon />}
                onClick={() => setCleanupDialogOpen(true)}
              >
                Limpiar Antiguas
              </Button>
              <Button
                variant="outlined"
                startIcon={<ExportIcon />}
                disabled={sessions.length === 0}
              >
                Exportar
              </Button>
            </Box>
          </Box>

          {/* Filtros */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Grid container spacing={2} alignItems="center">
              <Grid size={{ xs: 12, md: 3 }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Cámara</InputLabel>
                  <Select
                    value={filters.camera_id || ""}
                    onChange={(e) =>
                      setFilters((prev) => ({
                        ...prev,
                        camera_id: e.target.value || undefined,
                        page: 1,
                      }))
                    }
                    label="Cámara"
                  >
                    <MenuItem value="">Todas</MenuItem>
                    {Array.from(cameras.values()).map((camera) => (
                      <MenuItem key={camera.camera_id} value={camera.camera_id}>
                        {camera.display_name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, md: 3 }}>
                <LocalizationProvider
                  dateAdapter={AdapterDateFns}
                  adapterLocale={es}
                >
                  <DatePicker
                    label="Desde"
                    value={
                      filters.start_date ? new Date(filters.start_date) : null
                    }
                    onChange={(date) =>
                      setFilters((prev) => ({
                        ...prev,
                        start_date: date?.toISOString().split("T")[0],
                        page: 1,
                      }))
                    }
                    slotProps={{
                      textField: { size: "small", fullWidth: true },
                    }}
                  />
                </LocalizationProvider>
              </Grid>
              <Grid size={{ xs: 12, md: 3 }}>
                <LocalizationProvider
                  dateAdapter={AdapterDateFns}
                  adapterLocale={es}
                >
                  <DatePicker
                    label="Hasta"
                    value={filters.end_date ? new Date(filters.end_date) : null}
                    onChange={(date) =>
                      setFilters((prev) => ({
                        ...prev,
                        end_date: date?.toISOString().split("T")[0],
                        page: 1,
                      }))
                    }
                    slotProps={{
                      textField: { size: "small", fullWidth: true },
                    }}
                  />
                </LocalizationProvider>
              </Grid>
              <Grid size={{ xs: 12, md: 3 }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Estado</InputLabel>
                  <Select
                    value={filters.status || ""}
                    onChange={(e) =>
                      setFilters((prev) => ({
                        ...prev,
                        status: e.target.value || undefined,
                        page: 1,
                      }))
                    }
                    label="Estado"
                  >
                    <MenuItem value="">Todos</MenuItem>
                    <MenuItem value="completed">Completado</MenuItem>
                    <MenuItem value="error">Error</MenuItem>
                    <MenuItem value="stopped">Detenido</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Paper>

          {/* Tabla */}
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Cámara</TableCell>
                  <TableCell>Inicio</TableCell>
                  <TableCell>Fin</TableCell>
                  <TableCell>Duración</TableCell>
                  <TableCell>Estado</TableCell>
                  <TableCell align="right">Frames</TableCell>
                  <TableCell align="right">Datos</TableCell>
                  <TableCell align="right">FPS Prom.</TableCell>
                  <TableCell align="right">Bitrate Prom.</TableCell>
                  <TableCell align="center">Acciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sessions.map((session) => {
                  const camera = cameras.get(session.camera_id);
                  return (
                    <TableRow key={session.session_id}>
                      <TableCell>
                        {camera?.display_name || session.camera_id}
                      </TableCell>
                      <TableCell>
                        {formatDate(session.start_time, "dd/MM/yyyy HH:mm")}
                      </TableCell>
                      <TableCell>
                        {session.end_time
                          ? formatDate(session.end_time, "dd/MM/yyyy HH:mm")
                          : "-"}
                      </TableCell>
                      <TableCell>
                        {formatDuration(session.duration_seconds)}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={session.status}
                          size="small"
                          color={getStatusColor(session.status)}
                        />
                      </TableCell>
                      <TableCell align="right">
                        {session.total_frames.toLocaleString()}
                      </TableCell>
                      <TableCell align="right">
                        {formatBytes(session.total_bytes)}
                      </TableCell>
                      <TableCell align="right">
                        {session.average_fps.toFixed(1)}
                      </TableCell>
                      <TableCell align="right">
                        {formatBitrate(session.average_bitrate_kbps)}
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="Ver detalles">
                          <IconButton
                            size="small"
                            onClick={() => setSelectedSession(session)}
                          >
                            <InfoIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
            <TablePagination
              component="div"
              count={totalCount}
              page={filters.page! - 1}
              onPageChange={handleChangePage}
              rowsPerPage={filters.page_size!}
              onRowsPerPageChange={handleChangeRowsPerPage}
              labelRowsPerPage="Filas por página"
              labelDisplayedRows={({ from, to, count }) =>
                `${from}-${to} de ${count}`
              }
            />
          </TableContainer>

          {/* Diálogo de detalles */}
          <Dialog
            open={selectedSession !== null}
            onClose={() => setSelectedSession(null)}
            maxWidth="sm"
            fullWidth
          >
            <DialogTitle>Detalles de la Sesión</DialogTitle>
            <DialogContent>
              {selectedSession && (
                <Box sx={{ pt: 2 }}>
                  <Typography variant="body2" gutterBottom>
                    <strong>ID de Sesión:</strong> {selectedSession.session_id}
                  </Typography>
                  {selectedSession.error_message && (
                    <Typography variant="body2" color="error" sx={{ mt: 2 }}>
                      <strong>Error:</strong> {selectedSession.error_message}
                    </Typography>
                  )}
                </Box>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setSelectedSession(null)}>Cerrar</Button>
            </DialogActions>
          </Dialog>

          {/* Diálogo de limpieza */}
          <Dialog
            open={cleanupDialogOpen}
            onClose={() => setCleanupDialogOpen(false)}
            maxWidth="xs"
            fullWidth
          >
            <DialogTitle>Limpiar Historial Antiguo</DialogTitle>
            <DialogContent>
              <Typography variant="body2" sx={{ mb: 2 }}>
                Eliminar sesiones más antiguas de 90 días
              </Typography>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setCleanupDialogOpen(false)}>
                Cancelar
              </Button>
              <Button
                onClick={() => handleCleanup(90, true)}
                color="error"
                variant="contained"
              >
                Limpiar
              </Button>
            </DialogActions>
          </Dialog>
        </Box>
      </Fade>
    </Container>
  );
});

PublishingHistory.displayName = "PublishingHistory";

export default PublishingHistory;
