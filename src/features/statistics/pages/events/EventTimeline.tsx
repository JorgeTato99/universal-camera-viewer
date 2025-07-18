/**
 * 🎬 Event Timeline - Universal Camera Viewer
 * Línea de tiempo de eventos del sistema
 */

import React, { memo, useState, useCallback } from "react";
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  IconButton,
  Button,
  ToggleButton,
  ToggleButtonGroup,
  Collapse,
  Fade,
  Grow,
  Badge,
  Tooltip,
} from "@mui/material";
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent,
} from "@mui/lab";
import {
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as SuccessIcon,
  FilterList as FilterIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  Refresh as RefreshIcon,
  Download as ExportIcon,
  Videocam as CameraIcon,
  Link as ConnectionIcon,
  Security as SecurityIcon,
  Speed as PerformanceIcon,
} from "@mui/icons-material";
import { format } from "date-fns";
import { es } from "date-fns/locale";

type EventSeverity = "info" | "warning" | "error" | "critical";
type EventType = "all" | "connection" | "motion" | "tampering" | "system" | "performance";

interface SystemEvent {
  id: string;
  cameraId?: string;
  cameraName?: string;
  eventType: string;
  severity: EventSeverity;
  title: string;
  description: string;
  timestamp: string;
  acknowledged: boolean;
  acknowledgedBy?: string;
  metadata?: Record<string, any>;
}

const mockEvents: SystemEvent[] = [
  {
    id: "1",
    eventType: "connection",
    severity: "error",
    title: "Conexión perdida",
    description: "Se perdió la conexión con la cámara Entrada Principal",
    timestamp: new Date().toISOString(),
    acknowledged: false,
    cameraId: "cam1",
    cameraName: "Entrada Principal",
  },
  {
    id: "2",
    eventType: "motion",
    severity: "info",
    title: "Movimiento detectado",
    description: "Movimiento detectado en zona restringida",
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    acknowledged: true,
    acknowledgedBy: "admin",
    cameraId: "cam2",
    cameraName: "Almacén Sur",
  },
  {
    id: "3",
    eventType: "system",
    severity: "warning",
    title: "Alto uso de CPU",
    description: "El uso de CPU ha superado el 80% durante 5 minutos",
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    acknowledged: false,
  },
  {
    id: "4",
    eventType: "tampering",
    severity: "critical",
    title: "Posible manipulación",
    description: "Detectada posible manipulación de la cámara",
    timestamp: new Date(Date.now() - 10800000).toISOString(),
    acknowledged: false,
    cameraId: "cam3",
    cameraName: "Pasillo Central",
  },
];

const severityConfig = {
  info: { icon: <InfoIcon />, color: "#2196f3" },
  warning: { icon: <WarningIcon />, color: "#ff9800" },
  error: { icon: <ErrorIcon />, color: "#f44336" },
  critical: { icon: <ErrorIcon />, color: "#d32f2f" },
};

const eventTypeIcons = {
  connection: <ConnectionIcon />,
  motion: <CameraIcon />,
  tampering: <SecurityIcon />,
  system: <PerformanceIcon />,
  performance: <PerformanceIcon />,
};

const EventCard = memo(({ event, onAcknowledge }: { event: SystemEvent; onAcknowledge: (id: string) => void }) => {
  const [expanded, setExpanded] = useState(false);
  const config = severityConfig[event.severity];

  return (
    <Card
      sx={{
        mb: 2,
        borderLeft: 4,
        borderColor: config.color,
        backgroundColor: event.acknowledged ? "action.hover" : "background.paper",
      }}
    >
      <CardContent>
        <Box sx={{ display: "flex", alignItems: "flex-start", gap: 2 }}>
          <Box
            sx={{
              p: 1,
              borderRadius: 1,
              backgroundColor: `${config.color}15`,
              color: config.color,
            }}
          >
            {eventTypeIcons[event.eventType as keyof typeof eventTypeIcons] || config.icon}
          </Box>
          <Box sx={{ flexGrow: 1 }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
              <Typography variant="subtitle1" component="h3">
                {event.title}
              </Typography>
              <Chip
                label={event.severity}
                size="small"
                sx={{
                  backgroundColor: `${config.color}15`,
                  color: config.color,
                }}
              />
              {event.cameraName && (
                <Chip label={event.cameraName} size="small" variant="outlined" />
              )}
            </Box>
            <Typography variant="body2" color="text.secondary">
              {event.description}
            </Typography>
            <Box sx={{ display: "flex", alignItems: "center", gap: 2, mt: 1 }}>
              <Typography variant="caption" color="text.secondary">
                {format(new Date(event.timestamp), "dd/MM/yyyy HH:mm:ss", { locale: es })}
              </Typography>
              {event.acknowledged && (
                <Chip
                  label={`Reconocido por ${event.acknowledgedBy}`}
                  size="small"
                  color="success"
                  variant="outlined"
                />
              )}
            </Box>
            {event.metadata && (
              <>
                <IconButton
                  size="small"
                  onClick={() => setExpanded(!expanded)}
                  sx={{ mt: 1 }}
                >
                  {expanded ? <CollapseIcon /> : <ExpandIcon />}
                </IconButton>
                <Collapse in={expanded}>
                  <Box sx={{ mt: 2, p: 2, backgroundColor: "action.hover", borderRadius: 1 }}>
                    <Typography variant="caption" component="pre">
                      {JSON.stringify(event.metadata, null, 2)}
                    </Typography>
                  </Box>
                </Collapse>
              </>
            )}
          </Box>
          {!event.acknowledged && (
            <Button
              size="small"
              variant="outlined"
              onClick={() => onAcknowledge(event.id)}
            >
              Reconocer
            </Button>
          )}
        </Box>
      </CardContent>
    </Card>
  );
});

EventCard.displayName = "EventCard";

export const EventTimeline = memo(() => {
  const [events, setEvents] = useState<SystemEvent[]>(mockEvents);
  const [filterSeverity, setFilterSeverity] = useState<EventSeverity | "all">("all");
  const [filterType, setFilterType] = useState<EventType>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [viewMode, setViewMode] = useState<"timeline" | "list">("timeline");

  const handleAcknowledge = useCallback((eventId: string) => {
    setEvents((prev) =>
      prev.map((event) =>
        event.id === eventId
          ? { ...event, acknowledged: true, acknowledgedBy: "current_user" }
          : event
      )
    );
  }, []);

  const filteredEvents = events.filter((event) => {
    if (filterSeverity !== "all" && event.severity !== filterSeverity) return false;
    if (filterType !== "all" && event.eventType !== filterType) return false;
    if (searchTerm && !event.title.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !event.description.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  const unacknowledgedCount = events.filter((e) => !e.acknowledged).length;

  return (
    <Fade in timeout={600}>
      <Box>
        {/* Header */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
            <Typography variant="h6" component="h2" sx={{ flexGrow: 1 }}>
              Línea de Tiempo de Eventos
            </Typography>
            <Badge badgeContent={unacknowledgedCount} color="error">
              <Chip
                label={`${unacknowledgedCount} sin reconocer`}
                color={unacknowledgedCount > 0 ? "error" : "default"}
                variant="outlined"
              />
            </Badge>
          </Box>

          {/* Filters */}
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", alignItems: "center" }}>
              <TextField
                size="small"
                placeholder="Buscar eventos..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                sx={{ minWidth: 200 }}
              />
              
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Severidad</InputLabel>
                <Select
                  value={filterSeverity}
                  onChange={(e) => setFilterSeverity(e.target.value as EventSeverity | "all")}
                  label="Severidad"
                >
                  <MenuItem value="all">Todas</MenuItem>
                  <MenuItem value="info">Info</MenuItem>
                  <MenuItem value="warning">Advertencia</MenuItem>
                  <MenuItem value="error">Error</MenuItem>
                  <MenuItem value="critical">Crítico</MenuItem>
                </Select>
              </FormControl>

              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Tipo</InputLabel>
                <Select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value as EventType)}
                  label="Tipo"
                >
                  <MenuItem value="all">Todos</MenuItem>
                  <MenuItem value="connection">Conexión</MenuItem>
                  <MenuItem value="motion">Movimiento</MenuItem>
                  <MenuItem value="tampering">Manipulación</MenuItem>
                  <MenuItem value="system">Sistema</MenuItem>
                  <MenuItem value="performance">Rendimiento</MenuItem>
                </Select>
              </FormControl>

              <Box sx={{ ml: "auto", display: "flex", gap: 1 }}>
                <ToggleButtonGroup
                  value={viewMode}
                  exclusive
                  onChange={(_, value) => value && setViewMode(value)}
                  size="small"
                >
                  <ToggleButton value="timeline">Línea de Tiempo</ToggleButton>
                  <ToggleButton value="list">Lista</ToggleButton>
                </ToggleButtonGroup>

                <Tooltip title="Actualizar">
                  <IconButton size="small">
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Exportar">
                  <IconButton size="small">
                    <ExportIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
          </Paper>
        </Box>

        {/* Events Display */}
        {viewMode === "timeline" ? (
          <Grow in timeout={800}>
            <Paper sx={{ p: 3 }}>
              <Timeline position="alternate">
                {filteredEvents.map((event, index) => {
                  const config = severityConfig[event.severity];
                  return (
                    <TimelineItem key={event.id}>
                      <TimelineOppositeContent color="text.secondary">
                        {format(new Date(event.timestamp), "HH:mm", { locale: es })}
                      </TimelineOppositeContent>
                      <TimelineSeparator>
                        <TimelineDot sx={{ backgroundColor: config.color }}>
                          {config.icon}
                        </TimelineDot>
                        {index < filteredEvents.length - 1 && <TimelineConnector />}
                      </TimelineSeparator>
                      <TimelineContent>
                        <EventCard event={event} onAcknowledge={handleAcknowledge} />
                      </TimelineContent>
                    </TimelineItem>
                  );
                })}
              </Timeline>
            </Paper>
          </Grow>
        ) : (
          <Box>
            {filteredEvents.map((event, index) => (
              <Grow
                key={event.id}
                in
                timeout={800}
                style={{ transitionDelay: `${index * 100}ms` }}
              >
                <Box>
                  <EventCard event={event} onAcknowledge={handleAcknowledge} />
                </Box>
              </Grow>
            ))}
          </Box>
        )}

        {filteredEvents.length === 0 && (
          <Paper sx={{ p: 4, textAlign: "center" }}>
            <Typography color="text.secondary">
              No se encontraron eventos con los filtros aplicados
            </Typography>
          </Paper>
        )}
      </Box>
    </Fade>
  );
});

EventTimeline.displayName = "EventTimeline";

export default EventTimeline;