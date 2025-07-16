/**
 * 🎯 Port Scan Panel - Universal Camera Viewer
 * Panel para escaneo detallado de puertos en una IP específica
 */

import React, { useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  LinearProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  Alert,
  Collapse,
  TextField,
  FormControlLabel,
  Checkbox,
} from "@mui/material";
import {
  PortableWifiOff as PortIcon,
  CheckCircle as OpenIcon,
  Cancel as ClosedIcon,
  Refresh as RescanIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  ContentCopy as CopyIcon,
  Info as InfoIcon,
} from "@mui/icons-material";
import { colorTokens } from "../../../design-system/tokens";

interface Port {
  number: number;
  status: "open" | "closed" | "scanning" | "pending";
  service?: string;
  protocol?: string;
  confidence?: number;
}

interface PortScanPanelProps {
  selectedIP?: string;
  onComplete: () => void;
  onBack: () => void;
}

// Puertos comunes de cámaras por categoría
const PORT_CATEGORIES = {
  onvif: {
    name: "ONVIF",
    ports: [80, 8080, 2020, 8000],
    description: "Protocolo estándar para cámaras IP",
  },
  rtsp: {
    name: "RTSP",
    ports: [554, 8554, 5543, 5544],
    description: "Streaming de video en tiempo real",
  },
  http: {
    name: "HTTP/HTTPS",
    ports: [80, 443, 8080, 8081, 8443],
    description: "Interfaz web y API REST",
  },
  proprietary: {
    name: "Propietarios",
    ports: [37777, 37778, 34567, 34568],
    description: "Puertos específicos de fabricantes",
  },
};

export const PortScanPanel: React.FC<PortScanPanelProps> = ({
  selectedIP = "192.168.1.172",
  onComplete,
  onBack,
}) => {
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);
  const [customPorts, setCustomPorts] = useState("");
  const [includeCustom, setIncludeCustom] = useState(false);
  
  // Estado de puertos simulado
  const [ports, setPorts] = useState<Port[]>([
    { number: 80, status: "pending", service: "HTTP" },
    { number: 443, status: "pending", service: "HTTPS" },
    { number: 554, status: "pending", service: "RTSP" },
    { number: 2020, status: "pending", service: "ONVIF" },
    { number: 8080, status: "pending", service: "HTTP-ALT" },
    { number: 8000, status: "pending", service: "HTTP-ALT" },
    { number: 5543, status: "pending", service: "RTSP-ALT" },
    { number: 37777, status: "pending", service: "Dahua" },
  ]);

  /**
   * INTEGRACIÓN - Escanear Puertos
   * 
   * TODO: Conectar con el store/servicio
   * 
   * @example
   * const handleStartScan = async () => {
   *   const config: PortScanConfig = {
   *     ip: selectedIP,
   *     categories: {
   *       onvif: true,
   *       rtsp: true,
   *       http: true,
   *       proprietary: true,
   *     },
   *     customPorts: parseCustomPorts(customPorts),
   *   };
   *   
   *   try {
   *     setIsScanning(true);
   *     await useScannerStore.getState().startPortScan(config);
   *   } catch (error) {
   *     setIsScanning(false);
   *     // Mostrar error
   *   }
   * };
   */
  const handleStartScan = () => {
    setIsScanning(true);
    // TODO: Implementar llamada al store
    console.log("Iniciando escaneo de puertos para IP:", selectedIP);
    
    // Simular escaneo temporal
    setTimeout(() => {
      setPorts([
        { number: 80, status: "open", service: "HTTP", protocol: "ONVIF" },
        { number: 443, status: "closed", service: "HTTPS" },
        { number: 554, status: "open", service: "RTSP" },
        { number: 2020, status: "open", service: "ONVIF" },
        { number: 8080, status: "closed", service: "HTTP-ALT" },
      ]);
      setIsScanning(false);
      setScanProgress(100);
    }, 2000);
  };

  const handleStopScan = () => {
    setIsScanning(false);
    setScanProgress(0);
    // TODO: Llamar a cancelScan del store
  };

  const getPortStatusIcon = (status: Port["status"]) => {
    switch (status) {
      case "open":
        return <OpenIcon sx={{ color: colorTokens.status.connected, fontSize: 20 }} />;
      case "closed":
        return <ClosedIcon sx={{ color: colorTokens.status.error, fontSize: 20 }} />;
      case "scanning":
        return (
          <Box sx={{ width: 20, height: 20 }}>
            <LinearProgress
              sx={{
                borderRadius: 10,
                height: 4,
              }}
            />
          </Box>
        );
      default:
        return <Box sx={{ width: 20, height: 20, opacity: 0.3 }}>○</Box>;
    }
  };

  const openPorts = ports.filter((p) => p.status === "open");
  const scanComplete = ports.every((p) => p.status !== "pending" && p.status !== "scanning");

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
          Escaneo de Puertos
        </Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            IP Seleccionada:
          </Typography>
          <Chip
            label={selectedIP}
            size="small"
            sx={{
              fontFamily: "monospace",
              backgroundColor: (theme) =>
                theme.palette.mode === "dark"
                  ? colorTokens.neutral[800]
                  : colorTokens.neutral[100],
            }}
            deleteIcon={
              <Tooltip title="Copiar IP">
                <CopyIcon sx={{ fontSize: 16 }} />
              </Tooltip>
            }
            onDelete={() => navigator.clipboard.writeText(selectedIP)}
          />
        </Box>
        <Typography variant="caption" color="text.secondary">
          Analiza puertos específicos para identificar servicios de cámara disponibles
        </Typography>
      </Box>

      {/* Categorías de puertos */}
      <Paper
        variant="outlined"
        sx={{
          mb: 3,
          overflow: "hidden",
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="body2" sx={{ fontWeight: 500, mb: 2 }}>
            Puertos a Escanear
          </Typography>

          {Object.entries(PORT_CATEGORIES).map(([key, category]) => (
            <Box key={key} sx={{ mb: 1 }}>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  p: 1,
                  borderRadius: 1,
                  cursor: "pointer",
                  "&:hover": {
                    backgroundColor: (theme) => theme.palette.action.hover,
                  },
                }}
                onClick={() =>
                  setExpandedCategory(expandedCategory === key ? null : key)
                }
              >
                <IconButton size="small" sx={{ p: 0, mr: 1 }}>
                  {expandedCategory === key ? <CollapseIcon /> : <ExpandIcon />}
                </IconButton>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {category.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {category.description}
                  </Typography>
                </Box>
                <Chip
                  label={`${category.ports.length} puertos`}
                  size="small"
                  variant="outlined"
                />
              </Box>

              <Collapse in={expandedCategory === key}>
                <Box sx={{ pl: 5, pr: 2, pb: 1 }}>
                  <Typography
                    variant="caption"
                    sx={{
                      fontFamily: "monospace",
                      color: "text.secondary",
                    }}
                  >
                    {category.ports.join(", ")}
                  </Typography>
                </Box>
              </Collapse>
            </Box>
          ))}

          {/* Puertos personalizados */}
          <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: "divider" }}>
            <FormControlLabel
              control={
                <Checkbox
                  size="small"
                  checked={includeCustom}
                  onChange={(e) => setIncludeCustom(e.target.checked)}
                />
              }
              label="Incluir puertos personalizados"
            />
            {includeCustom && (
              <TextField
                fullWidth
                size="small"
                placeholder="Ej: 8081, 9000-9010, 5000"
                value={customPorts}
                onChange={(e) => setCustomPorts(e.target.value)}
                sx={{
                  mt: 1,
                  "& .MuiOutlinedInput-root": {
                    fontFamily: "monospace",
                  },
                }}
                helperText="Separados por comas, soporta rangos"
              />
            )}
          </Box>
        </Box>
      </Paper>

      {/* Progreso del escaneo */}
      {isScanning && (
        <Paper
          sx={{
            p: 2,
            mb: 3,
            backgroundColor: colorTokens.primary[50],
            border: `1px solid ${colorTokens.primary[200]}`,
          }}
        >
          <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              Escaneando puertos...
            </Typography>
            <Typography variant="body2" color="primary">
              {scanProgress}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={scanProgress}
            sx={{
              height: 6,
              borderRadius: 3,
              backgroundColor: colorTokens.primary[100],
              "& .MuiLinearProgress-bar": {
                borderRadius: 3,
                backgroundColor: colorTokens.primary[500],
              },
            }}
          />
        </Paper>
      )}

      {/* Resultados del escaneo */}
      {ports.some(p => p.status !== "pending") && (
        <Paper variant="outlined" sx={{ mb: 3 }}>
          <Box sx={{ p: 2, borderBottom: 1, borderColor: "divider" }}>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              Resultados del Escaneo
            </Typography>
          </Box>
          <TableContainer sx={{ maxHeight: 300 }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Puerto</TableCell>
                  <TableCell>Estado</TableCell>
                  <TableCell>Servicio</TableCell>
                  <TableCell>Protocolo</TableCell>
                  <TableCell align="right">Acciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {ports.map((port) => (
                  <TableRow
                    key={port.number}
                    sx={{
                      "&:hover": {
                        backgroundColor: (theme) => theme.palette.action.hover,
                      },
                    }}
                  >
                    <TableCell>
                      <Typography
                        variant="body2"
                        sx={{ fontFamily: "monospace", fontWeight: 500 }}
                      >
                        {port.number}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        {getPortStatusIcon(port.status)}
                        <Typography
                          variant="caption"
                          sx={{
                            color:
                              port.status === "open"
                                ? colorTokens.status.connected
                                : port.status === "closed"
                                ? colorTokens.status.error
                                : "text.secondary",
                          }}
                        >
                          {port.status === "open"
                            ? "Abierto"
                            : port.status === "closed"
                            ? "Cerrado"
                            : port.status === "scanning"
                            ? "Escaneando..."
                            : "Pendiente"}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">{port.service || "-"}</Typography>
                    </TableCell>
                    <TableCell>
                      {port.protocol && (
                        <Chip
                          label={port.protocol}
                          size="small"
                          sx={{ fontSize: "0.7rem" }}
                        />
                      )}
                    </TableCell>
                    <TableCell align="right">
                      {port.status === "open" && (
                        <Tooltip title="Más información">
                          <IconButton size="small">
                            <InfoIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Resumen de resultados */}
      {scanComplete && openPorts.length > 0 && (
        <Alert
          severity="success"
          variant="outlined"
          sx={{ mb: 3 }}
          icon={<PortIcon />}
        >
          Se encontraron {openPorts.length} puerto(s) abierto(s). 
          {openPorts.some(p => [80, 2020, 8000].includes(p.number)) &&
            " Se detectó soporte ONVIF probable."}
          {openPorts.some(p => [554, 5543].includes(p.number)) &&
            " Se detectó soporte RTSP."}
        </Alert>
      )}

      {/* Botones de acción */}
      <Box sx={{ display: "flex", gap: 2 }}>
        <Button variant="outlined" onClick={onBack}>
          Atrás
        </Button>
        {!isScanning ? (
          <>
            <Button
              variant="contained"
              fullWidth
              startIcon={<PortIcon />}
              onClick={handleStartScan}
            >
              {scanComplete ? "Re-escanear Puertos" : "Iniciar Escaneo"}
            </Button>
            {openPorts.length > 0 && (
              <Button
                variant="contained"
                color="success"
                onClick={onComplete}
                sx={{ minWidth: 140 }}
              >
                Continuar
              </Button>
            )}
          </>
        ) : (
          <Button
            variant="outlined"
            fullWidth
            color="error"
            onClick={handleStopScan}
          >
            Detener Escaneo
          </Button>
        )}
      </Box>
    </Box>
  );
};