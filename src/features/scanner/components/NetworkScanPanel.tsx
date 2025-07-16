/**
 * 🎯 Network Scan Panel - Universal Camera Viewer
 * Panel para escaneo general de la red local
 */

import React, { useState } from "react";
import {
  Box,
  Typography,
  TextField,
  Button,
  LinearProgress,
  Alert,
  Chip,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Divider,
  IconButton,
  Tooltip,
  Paper,
  keyframes,
  Fade,
  Grow,
  alpha,
} from "@mui/material";
import {
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Info as InfoIcon,
  NetworkCheck as NetworkIcon,
  Speed as SpeedIcon,
  Timer as TimerIcon,
} from "@mui/icons-material";
import { colorTokens, spacingTokens, borderTokens } from "../../../design-system/tokens";

// Animaciones
const scanAnimation = keyframes`
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
`;

const fadeInUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

interface NetworkScanPanelProps {
  onComplete: () => void;
  isScanning: boolean;
  progress: number;
}

export const NetworkScanPanel: React.FC<NetworkScanPanelProps> = ({
  onComplete,
  isScanning,
  progress,
}) => {
  const [scanMode, setScanMode] = useState<"auto" | "manual">("auto");
  const [ipRange, setIpRange] = useState("192.168.1.0/24");
  const [scanSpeed, setScanSpeed] = useState<"fast" | "normal" | "thorough">("normal");
  const [currentIP, setCurrentIP] = useState("");
  const [devicesFound, setDevicesFound] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);

  /**
   * Ver documentación completa de integración en líneas 107-149
   */
  const handleStartScan = () => {
    // 🔧 MOCK: Iniciar escaneo - VER IMPLEMENTACIÓN COMPLETA EN LÍNEA 107
    console.log("🔧 MOCK: Iniciando escaneo de red...", {
      mode: scanMode,
      ipRange,
      speed: scanSpeed,
    });
  };

  /**
   * 🚀 INTEGRACIÓN PENDIENTE - Sistema de Escaneo de Red
   * 
   * TODO: Conectar con backend de escaneo
   * 
   * ENDPOINTS BACKEND:
   * - POST /api/v2/scanner/network/start
   *   Body: { mode: 'auto'|'manual', ipRange?: string, scanSpeed: string, ports: string[] }
   * - POST /api/v2/scanner/network/stop
   *   Body: { scanId: string }
   * - WS eventos: 'scanner:progress', 'scanner:device_found'
   * 
   * IMPLEMENTACIÓN handleStartScan:
   * ```typescript
   * const handleStartScan = async () => {
   *   setIsScanning(true);
   *   try {
   *     const config = {
   *       mode: scanMode,
   *       ipRange: scanMode === 'manual' ? ipRange : undefined,
   *       scanSpeed,
   *       ports: getScanSpeedConfig().ports.split(', ')
   *     };
   *     
   *     const { scanId } = await scannerService.startNetworkScan(config);
   *     setScanId(scanId);
   *     
   *     // Escuchar eventos WebSocket
   *     socket.on(`scanner:progress:${scanId}`, (progress) => {
   *       setScanProgress(progress.percentage);
   *     });
   *     
   *     socket.on(`scanner:device_found:${scanId}`, (device) => {
   *       setDevicesFound(prev => prev + 1);
   *       onDeviceFound?.(device);
   *     });
   *   } catch (error) {
   *     showNotification({ type: 'error', message: 'Error al iniciar escaneo' });
   *     setIsScanning(false);
   *   }
   * };
   * ```
   */
  const handleStopScan = () => {
    /**
     * TODO: Implementar cancelación de escaneo
     * ```typescript
     * await scannerService.stopNetworkScan(scanId);
     * socket.off(`scanner:progress:${scanId}`);
     * socket.off(`scanner:device_found:${scanId}`);
     * ```
     */
    console.log("🔧 MOCK: Deteniendo escaneo - IMPLEMENTAR");
  };

  const getScanSpeedConfig = () => {
    switch (scanSpeed) {
      case "fast":
        return { 
          label: "Rápido", 
          description: "Solo puertos comunes de cámaras",
          color: colorTokens.status.connecting,
          ports: "80, 554, 8080, 2020, 8000"
        };
      case "thorough":
        return { 
          label: "Exhaustivo", 
          description: "Escaneo completo de puertos",
          color: colorTokens.status.error,
          ports: "1-10000"
        };
      default:
        return { 
          label: "Normal", 
          description: "Puertos estándar de cámaras IP",
          color: colorTokens.primary[500],
          ports: "80, 443, 554, 8080, 8081, 2020, 8000, 5000, 5543"
        };
    }
  };

  const speedConfig = getScanSpeedConfig();

  return (
    <Box>
      {/* Título y descripción */}
      <Fade in timeout={500}>
        <Box sx={{ mb: 3, animation: `${fadeInUp} 0.6s ease-out` }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
            Escaneo de Red Local
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Busca dispositivos en tu red que puedan ser cámaras IP analizando 
            puertos comunes y patrones de respuesta.
          </Typography>
        </Box>
      </Fade>

      {/* Modo de escaneo */}
      <Grow in timeout={600} style={{ transformOrigin: "top" }}>
        <Paper
          variant="outlined"
          sx={{
            p: 2,
            mb: 3,
            backgroundColor: (theme) =>
              theme.palette.mode === "dark"
                ? "rgba(255, 255, 255, 0.02)"
                : "rgba(0, 0, 0, 0.01)",
            borderRadius: borderTokens.radius.md,
            transition: "all 0.3s ease",
            "&:hover": {
              borderColor: colorTokens.primary[200],
              boxShadow: `0 0 0 1px ${alpha(colorTokens.primary[500], 0.1)}`,
            },
          }}
        >
        <FormControl component="fieldset">
          <FormLabel 
            component="legend" 
            sx={{ 
              fontSize: "0.875rem",
              fontWeight: 500,
              mb: 1
            }}
          >
            Modo de Escaneo
          </FormLabel>
          <RadioGroup
            row
            value={scanMode}
            onChange={(e) => setScanMode(e.target.value as "auto" | "manual")}
          >
            <FormControlLabel
              value="auto"
              control={<Radio size="small" />}
              label={
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    Automático
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Detecta tu red local automáticamente
                  </Typography>
                </Box>
              }
              sx={{ mr: 4 }}
            />
            <FormControlLabel
              value="manual"
              control={<Radio size="small" />}
              label={
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    Manual
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Especifica el rango de IPs
                  </Typography>
                </Box>
              }
            />
          </RadioGroup>
        </FormControl>

        {/* Campo de rango IP para modo manual */}
        <Fade in={scanMode === "manual"} unmountOnExit>
          <Box sx={{ mt: 2 }}>
            <TextField
              fullWidth
              size="small"
              label="Rango de IP (CIDR)"
              value={ipRange}
              onChange={(e) => setIpRange(e.target.value)}
              placeholder="192.168.1.0/24"
              helperText="Formato: 192.168.1.0/24 para escanear 192.168.1.1-254"
              disabled={isScanning}
              sx={{
                "& .MuiOutlinedInput-root": {
                  fontFamily: "monospace",
                },
              }}
            />
          </Box>
        </Fade>
        </Paper>
      </Grow>

      {/* Velocidad de escaneo */}
      <Grow in timeout={700} style={{ transformOrigin: "top" }}>
        <Paper
          variant="outlined"
          sx={{
            p: 2,
            mb: 3,
            backgroundColor: (theme) =>
              theme.palette.mode === "dark"
                ? "rgba(255, 255, 255, 0.02)"
                : "rgba(0, 0, 0, 0.01)",
            borderRadius: borderTokens.radius.md,
            transition: "all 0.3s ease",
            "&:hover": {
              borderColor: colorTokens.primary[200],
              boxShadow: `0 0 0 1px ${alpha(colorTokens.primary[500], 0.1)}`,
            },
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
            <SpeedIcon 
              fontSize="small" 
              sx={{ 
                color: colorTokens.primary[500],
                transition: "transform 0.3s ease",
              }} 
            />
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              Velocidad de Escaneo
            </Typography>
            <Tooltip title="La velocidad afecta la precisión y el tiempo de escaneo" arrow>
              <IconButton 
                size="small"
                sx={{
                  transition: "all 0.3s ease",
                  "&:hover": {
                    backgroundColor: alpha(colorTokens.primary[500], 0.1),
                  },
                }}
              >
                <InfoIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>

        <RadioGroup
          value={scanSpeed}
          onChange={(e) => setScanSpeed(e.target.value as any)}
        >
          {["fast", "normal", "thorough"].map((speed) => {
            const config = speed === "fast" 
              ? { label: "Rápido", description: "Solo puertos comunes", time: "~1 min" }
              : speed === "thorough"
              ? { label: "Exhaustivo", description: "Escaneo completo", time: "~10 min" }
              : { label: "Normal", description: "Balance óptimo", time: "~3 min" };
            
            return (
              <FormControlLabel
                key={speed}
                value={speed}
                control={<Radio size="small" />}
                label={
                  <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {config.label}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {config.description}
                      </Typography>
                    </Box>
                    <Chip
                      label={config.time}
                      size="small"
                      variant="outlined"
                      sx={{ fontSize: "0.7rem" }}
                    />
                  </Box>
                }
                sx={{ mb: 1 }}
                disabled={isScanning}
              />
            );
          })}
        </RadioGroup>

        {/* Información de puertos a escanear */}
        <Box
          sx={{
            mt: 2,
            p: 1.5,
            backgroundColor: (theme) =>
              theme.palette.mode === "dark"
                ? "rgba(255, 255, 255, 0.05)"
                : "rgba(0, 0, 0, 0.03)",
            borderRadius: 1,
            border: (theme) => `1px solid ${theme.palette.divider}`,
          }}
        >
          <Typography variant="caption" color="text.secondary">
            Puertos a escanear: {speedConfig.ports}
          </Typography>
        </Box>
      </Paper>
      </Grow>

      {/* Estado del escaneo */}
      {isScanning && (
        <Paper
          sx={{
            p: 2,
            mb: 3,
            backgroundColor: colorTokens.primary[50],
            border: `1px solid ${colorTokens.primary[200]}`,
          }}
        >
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                Escaneando red...
              </Typography>
              <Typography variant="body2" color="primary">
                {progress}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={progress}
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
          </Box>

          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr",
              gap: 2,
            }}
          >
            <Box>
              <Typography variant="caption" color="text.secondary">
                IP Actual
              </Typography>
              <Typography
                variant="body2"
                sx={{ fontFamily: "monospace", fontWeight: 500 }}
              >
                {currentIP || "192.168.1.1"}
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Dispositivos
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {devicesFound}
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Tiempo
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {Math.floor(elapsedTime / 60)}:{(elapsedTime % 60).toString().padStart(2, "0")}
              </Typography>
            </Box>
          </Box>
        </Paper>
      )}

      {/* Alert informativo */}
      <Fade in={!isScanning} unmountOnExit>
        <Alert
          severity="info"
          variant="outlined"
          sx={{ 
            mb: 3,
            borderRadius: borderTokens.radius.md,
            "& .MuiAlert-icon": {
              color: colorTokens.primary[500],
            },
          }}
          icon={<NetworkIcon />}
        >
          El escaneo analizará cada IP en el rango especificado buscando puertos 
          abiertos comúnmente utilizados por cámaras IP. Los dispositivos con mayor 
          probabilidad aparecerán primero en los resultados.
        </Alert>
      </Fade>

      {/* Botones de acción */}
      <Box sx={{ display: "flex", gap: 2 }}>
        {!isScanning ? (
          <Button
            variant="contained"
            fullWidth
            startIcon={<StartIcon />}
            onClick={handleStartScan}
            sx={{
              height: 48,
              fontSize: "0.9rem",
              fontWeight: 500,
              transition: "all 0.3s ease",
              "&:hover": {
                transform: "translateY(-2px)",
                boxShadow: theme => theme.shadows[8],
              },
              "&:active": {
                transform: "translateY(0)",
              },
            }}
          >
            Iniciar Escaneo
          </Button>
        ) : (
          <>
            <Button
              variant="outlined"
              fullWidth
              startIcon={<StopIcon />}
              onClick={handleStopScan}
              color="error"
              sx={{
                height: 48,
                fontSize: "0.9rem",
                fontWeight: 500,
              }}
            >
              Detener Escaneo
            </Button>
            <Button
              variant="contained"
              onClick={onComplete}
              disabled={devicesFound === 0}
              sx={{
                height: 48,
                fontSize: "0.9rem",
                fontWeight: 500,
                minWidth: 140,
              }}
            >
              Continuar
            </Button>
          </>
        )}
      </Box>
    </Box>
  );
};