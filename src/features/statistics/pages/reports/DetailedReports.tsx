/**
 * 📑 Detailed Reports - Universal Camera Viewer
 * Reportes detallados y exportación de datos
 */

import React, { memo, useState, useCallback } from "react";
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Chip,
  IconButton,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondary,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stepper,
  Step,
  StepLabel,
  Alert,
  Fade,
  Grow,
} from "@mui/material";
import {
  Description as ReportIcon,
  Schedule as ScheduleIcon,
  Download as DownloadIcon,
  Email as EmailIcon,
  PictureAsPdf as PdfIcon,
  TableChart as ExcelIcon,
  Code as JsonIcon,
  CalendarToday as CalendarIcon,
  Timer as TimeIcon,
  CheckCircle as CheckIcon,
  Add as AddIcon,
  Preview as PreviewIcon,
} from "@mui/icons-material";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import { es } from "date-fns/locale";

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  category: "performance" | "connections" | "events" | "inventory";
  icon: React.ReactNode;
  fields: string[];
  formats: ("pdf" | "excel" | "json")[];
}

interface ScheduledReport {
  id: string;
  templateId: string;
  name: string;
  frequency: "daily" | "weekly" | "monthly";
  nextRun: string;
  recipients: string[];
  format: "pdf" | "excel" | "json";
  enabled: boolean;
}

const reportTemplates: ReportTemplate[] = [
  {
    id: "performance-summary",
    name: "Resumen de Rendimiento",
    description: "Métricas de FPS, latencia y uso de recursos",
    category: "performance",
    icon: <TimeIcon />,
    fields: ["fps", "latency", "cpu", "memory", "bandwidth"],
    formats: ["pdf", "excel", "json"],
  },
  {
    id: "connection-history",
    name: "Historial de Conexiones",
    description: "Registro detallado de todas las conexiones",
    category: "connections",
    icon: <TimeIcon />,
    fields: ["timestamp", "camera", "duration", "status", "bytes"],
    formats: ["excel", "json"],
  },
  {
    id: "event-log",
    name: "Registro de Eventos",
    description: "Todos los eventos del sistema con filtros",
    category: "events",
    icon: <ReportIcon />,
    fields: ["timestamp", "type", "severity", "camera", "description"],
    formats: ["pdf", "excel", "json"],
  },
  {
    id: "camera-inventory",
    name: "Inventario de Cámaras",
    description: "Lista completa de cámaras con especificaciones",
    category: "inventory",
    icon: <ReportIcon />,
    fields: ["brand", "model", "ip", "status", "lastSeen"],
    formats: ["pdf", "excel"],
  },
];

const mockScheduledReports: ScheduledReport[] = [
  {
    id: "1",
    templateId: "performance-summary",
    name: "Reporte Semanal de Rendimiento",
    frequency: "weekly",
    nextRun: new Date(Date.now() + 604800000).toISOString(),
    recipients: ["admin@example.com", "supervisor@example.com"],
    format: "pdf",
    enabled: true,
  },
  {
    id: "2",
    templateId: "event-log",
    name: "Eventos Críticos Diarios",
    frequency: "daily",
    nextRun: new Date(Date.now() + 86400000).toISOString(),
    recipients: ["security@example.com"],
    format: "excel",
    enabled: true,
  },
];

export const DetailedReports = memo(() => {
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null);
  const [scheduledReports, setScheduledReports] = useState<ScheduledReport[]>(mockScheduledReports);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [dateRange, setDateRange] = useState<{ start: Date | null; end: Date | null }>({
    start: new Date(Date.now() - 604800000), // 7 days ago
    end: new Date(),
  });

  const handleGenerateReport = useCallback((template: ReportTemplate, format: string) => {
    // TODO: Implementar generación de reportes
    console.log("Generate report:", template.id, format);
  }, []);

  const handleCreateScheduled = useCallback(() => {
    setCreateDialogOpen(true);
    setActiveStep(0);
  }, []);

  const handleDeleteScheduled = useCallback((reportId: string) => {
    setScheduledReports((prev) => prev.filter((r) => r.id !== reportId));
  }, []);

  const handleToggleScheduled = useCallback((reportId: string) => {
    setScheduledReports((prev) =>
      prev.map((r) => (r.id === reportId ? { ...r, enabled: !r.enabled } : r))
    );
  }, []);

  const getFormatIcon = (format: string) => {
    switch (format) {
      case "pdf":
        return <PdfIcon />;
      case "excel":
        return <ExcelIcon />;
      case "json":
        return <JsonIcon />;
      default:
        return <ReportIcon />;
    }
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={es}>
      <Fade in timeout={600}>
        <Box>
          {/* Header */}
          <Typography variant="h6" component="h2" gutterBottom>
            Reportes Detallados
          </Typography>

          {/* Report Templates */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="subtitle1" gutterBottom sx={{ mb: 2 }}>
              Plantillas de Reportes Disponibles
            </Typography>
            <Grid container spacing={3}>
              {reportTemplates.map((template, index) => (
                <Grid size={{ xs: 12, md: 6 }} key={template.id}>
                  <Grow in timeout={800} style={{ transitionDelay: `${index * 100}ms` }}>
                    <Card
                      sx={{
                        height: "100%",
                        display: "flex",
                        flexDirection: "column",
                        transition: "transform 0.2s",
                        "&:hover": {
                          transform: "translateY(-4px)",
                          boxShadow: 4,
                        },
                      }}
                    >
                      <CardContent sx={{ flexGrow: 1 }}>
                        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                          <Box
                            sx={{
                              p: 1,
                              borderRadius: 2,
                              backgroundColor: "primary.light",
                              color: "primary.contrastText",
                              mr: 2,
                            }}
                          >
                            {template.icon}
                          </Box>
                          <Box sx={{ flexGrow: 1 }}>
                            <Typography variant="h6" component="h3">
                              {template.name}
                            </Typography>
                            <Chip
                              label={template.category}
                              size="small"
                              variant="outlined"
                              sx={{ mt: 0.5 }}
                            />
                          </Box>
                        </Box>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          {template.description}
                        </Typography>
                        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                          <Typography variant="caption" color="text.secondary">
                            Formatos:
                          </Typography>
                          {template.formats.map((format) => (
                            <Chip
                              key={format}
                              icon={getFormatIcon(format)}
                              label={format.toUpperCase()}
                              size="small"
                              variant="outlined"
                            />
                          ))}
                        </Box>
                      </CardContent>
                      <CardActions>
                        <Button
                          size="small"
                          startIcon={<PreviewIcon />}
                          onClick={() => setSelectedTemplate(template)}
                        >
                          Configurar
                        </Button>
                        <Box sx={{ ml: "auto", display: "flex", gap: 1 }}>
                          {template.formats.map((format) => (
                            <Tooltip key={format} title={`Generar ${format.toUpperCase()}`}>
                              <IconButton
                                size="small"
                                onClick={() => handleGenerateReport(template, format)}
                              >
                                {getFormatIcon(format)}
                              </IconButton>
                            </Tooltip>
                          ))}
                        </Box>
                      </CardActions>
                    </Card>
                  </Grow>
                </Grid>
              ))}
            </Grid>
          </Box>

          <Divider sx={{ my: 4 }} />

          {/* Scheduled Reports */}
          <Box>
            <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
              <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
                Reportes Programados
              </Typography>
              <Button
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={handleCreateScheduled}
                size="small"
              >
                Programar Reporte
              </Button>
            </Box>

            <Grid container spacing={2}>
              {scheduledReports.map((report, index) => {
                const template = reportTemplates.find((t) => t.id === report.templateId);
                return (
                  <Grid size={12} key={report.id}>
                    <Grow in timeout={800} style={{ transitionDelay: `${index * 100}ms` }}>
                      <Paper sx={{ p: 2 }}>
                        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                          <Box
                            sx={{
                              p: 1,
                              borderRadius: 1,
                              backgroundColor: report.enabled ? "success.light" : "action.hover",
                              color: report.enabled ? "success.contrastText" : "text.secondary",
                            }}
                          >
                            <ScheduleIcon />
                          </Box>
                          <Box sx={{ flexGrow: 1 }}>
                            <Typography variant="subtitle2">{report.name}</Typography>
                            <Box sx={{ display: "flex", gap: 2, mt: 0.5 }}>
                              <Chip
                                label={template?.name || "Unknown"}
                                size="small"
                                variant="outlined"
                              />
                              <Chip
                                label={report.frequency}
                                size="small"
                                icon={<CalendarIcon />}
                              />
                              <Chip
                                label={report.format.toUpperCase()}
                                size="small"
                                icon={getFormatIcon(report.format)}
                              />
                              <Chip
                                label={`${report.recipients.length} destinatarios`}
                                size="small"
                                icon={<EmailIcon />}
                              />
                            </Box>
                            <Typography variant="caption" color="text.secondary">
                              Próxima ejecución: {new Date(report.nextRun).toLocaleString("es-ES")}
                            </Typography>
                          </Box>
                          <Button
                            variant={report.enabled ? "outlined" : "contained"}
                            size="small"
                            onClick={() => handleToggleScheduled(report.id)}
                          >
                            {report.enabled ? "Pausar" : "Activar"}
                          </Button>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDeleteScheduled(report.id)}
                          >
                            <DownloadIcon />
                          </IconButton>
                        </Box>
                      </Paper>
                    </Grow>
                  </Grid>
                );
              })}
            </Grid>

            {scheduledReports.length === 0 && (
              <Paper sx={{ p: 4, textAlign: "center", mt: 2 }}>
                <Typography color="text.secondary">
                  No hay reportes programados. Crea uno nuevo para recibir informes periódicos.
                </Typography>
              </Paper>
            )}
          </Box>

          {/* Report Configuration Dialog */}
          {selectedTemplate && (
            <Dialog
              open={Boolean(selectedTemplate)}
              onClose={() => setSelectedTemplate(null)}
              maxWidth="md"
              fullWidth
            >
              <DialogTitle>Configurar Reporte: {selectedTemplate.name}</DialogTitle>
              <DialogContent>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Rango de Fechas
                  </Typography>
                  <Box sx={{ display: "flex", gap: 2, mb: 3 }}>
                    <DatePicker
                      label="Fecha Inicio"
                      value={dateRange.start}
                      onChange={(date) => setDateRange((prev) => ({ ...prev, start: date }))}
                      slotProps={{ textField: { fullWidth: true } }}
                    />
                    <DatePicker
                      label="Fecha Fin"
                      value={dateRange.end}
                      onChange={(date) => setDateRange((prev) => ({ ...prev, end: date }))}
                      slotProps={{ textField: { fullWidth: true } }}
                    />
                  </Box>

                  <Typography variant="subtitle2" gutterBottom>
                    Campos a Incluir
                  </Typography>
                  <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 3 }}>
                    {selectedTemplate.fields.map((field) => (
                      <Chip key={field} label={field} icon={<CheckIcon />} color="primary" />
                    ))}
                  </Box>

                  <Alert severity="info">
                    El reporte incluirá todos los datos disponibles para el período seleccionado.
                  </Alert>
                </Box>
              </DialogContent>
              <DialogActions>
                <Button onClick={() => setSelectedTemplate(null)}>Cancelar</Button>
                <Button
                  variant="contained"
                  startIcon={<DownloadIcon />}
                  onClick={() => {
                    handleGenerateReport(selectedTemplate, selectedTemplate.formats[0]);
                    setSelectedTemplate(null);
                  }}
                >
                  Generar Reporte
                </Button>
              </DialogActions>
            </Dialog>
          )}

          {/* Create Scheduled Report Dialog */}
          <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
            <DialogTitle>Programar Nuevo Reporte</DialogTitle>
            <DialogContent>
              <Stepper activeStep={activeStep} sx={{ my: 3 }}>
                <Step>
                  <StepLabel>Seleccionar Plantilla</StepLabel>
                </Step>
                <Step>
                  <StepLabel>Configurar Frecuencia</StepLabel>
                </Step>
                <Step>
                  <StepLabel>Destinatarios</StepLabel>
                </Step>
              </Stepper>
              {/* TODO: Implementar pasos del wizard */}
              <Alert severity="info" sx={{ mt: 2 }}>
                Funcionalidad de programación de reportes en desarrollo.
              </Alert>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setCreateDialogOpen(false)}>Cancelar</Button>
              <Button variant="contained" disabled>
                Programar
              </Button>
            </DialogActions>
          </Dialog>
        </Box>
      </Fade>
    </LocalizationProvider>
  );
});

DetailedReports.displayName = "DetailedReports";

export default DetailedReports;