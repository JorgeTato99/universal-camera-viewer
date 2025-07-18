/**
 * 🎯 Camera Card Component - Universal Camera Viewer
 * Card individual para cada cámara con información completa
 */

import React, { memo, useCallback } from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  Button,
  Tooltip,
} from "@mui/material";
import {
  Settings as SettingsIcon,
  CameraAlt as CameraAltIcon,
  PowerSettingsNew as ConnectIcon,
  PowerOff as DisconnectIcon,
  Circle as StatusIcon,
  NetworkCheck as NetworkIcon,
  Timer as TimerIcon,
  Speed as SpeedIcon,
  HealthAndSafety as HealthIcon,
} from "@mui/icons-material";
import { cardStyles } from "../../../design-system/components";
import { colorTokens } from "../../../design-system/tokens";
import { VideoStream } from "./VideoStream";

interface CameraCardProps {
  cameraId: string;
  name?: string;
  status?: "connected" | "disconnected" | "connecting" | "error";
  aspectRatio?: "16:9" | "4:3";
  ip?: string;
  fps?: number;
  latency?: number; // MS
  connectedTime?: string; // Tiempo conectado
  onConnect?: () => void;
  onDisconnect?: () => void;
  onSettings?: () => void;
  onCapture?: () => void;
}

// Componente optimizado con memo para evitar re-renders innecesarios
export const CameraCard = memo<CameraCardProps>(({
  cameraId,
  name = `Cámara ${cameraId}`,
  status = "disconnected",
  ip = "192.168.1.100",
  onConnect,
  onDisconnect,
  onSettings,
  onCapture,
}) => {
  // Estado local para métricas del streaming
  const [streamMetrics, setStreamMetrics] = React.useState({
    fps: 0,
    latency: 0,
    isStreaming: false,
    latencyType: 'simulated' as 'real' | 'simulated',
    avgFps: 0,
    avgLatency: 0,
    healthScore: 0,
    rtt: 0,
    avgRtt: 0,
    minRtt: 0,
    maxRtt: 0,
  });
  
  // Estado para el tiempo conectado
  const [connectionTime, setConnectionTime] = React.useState<Date | null>(null);
  const [displayTime, setDisplayTime] = React.useState("--:--:--");
  
  // Definir isConnected e isConnecting antes de usarlos
  const isConnected = status === "connected";
  const isConnecting = status === "connecting";
  
  // Resetear métricas cuando se desconecta
  React.useEffect(() => {
    if (!isConnected) {
      setStreamMetrics({
        fps: 0,
        latency: 0,
        isStreaming: false,
        latencyType: 'simulated',
        avgFps: 0,
        avgLatency: 0,
        healthScore: 0,
        rtt: 0,
        avgRtt: 0,
        minRtt: 0,
        maxRtt: 0,
      });
      setConnectionTime(null);
      setDisplayTime("--:--:--");
    }
  }, [isConnected]);
  
  const getStatusColor = () => {
    switch (status) {
      case "connected":
        return colorTokens.status.connected;
      case "connecting":
        return colorTokens.status.connecting;
      case "error":
        return colorTokens.status.error;
      default:
        return colorTokens.status.disconnected;
    }
  };

  const getStatusLabel = () => {
    switch (status) {
      case "connected":
        return "Conectada";
      case "connecting":
        return "Conectando...";
      case "error":
        return "Error";
      default:
        return "Desconectada";
    }
  };
  
  // Efecto para actualizar el tiempo cuando se conecta/desconecta
  React.useEffect(() => {
    if (streamMetrics.isStreaming && !connectionTime) {
      setConnectionTime(new Date());
    } else if (!streamMetrics.isStreaming && connectionTime) {
      // Solo resetear si había una conexión previa
      setConnectionTime(null);
      setDisplayTime("--:--:--");
    }
  }, [streamMetrics.isStreaming, connectionTime]);
  
  // Efecto para actualizar el contador de tiempo
  React.useEffect(() => {
    if (!connectionTime) return;
    
    const updateTimer = () => {
      const now = new Date();
      const elapsed = now.getTime() - connectionTime.getTime();
      
      const hours = Math.floor(elapsed / 3600000);
      const minutes = Math.floor((elapsed % 3600000) / 60000);
      const seconds = Math.floor((elapsed % 60000) / 1000);
      
      const formatted = `${hours.toString().padStart(2, '0')}:${minutes
        .toString()
        .padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
      
      setDisplayTime(formatted);
    };
    
    // Actualizar inmediatamente
    updateTimer();
    
    // Actualizar cada segundo
    const interval = setInterval(updateTimer, 1000);
    
    return () => clearInterval(interval);
  }, [connectionTime]);

  return (
    <Card
      sx={{
        ...cardStyles.camera,
        // Asegurar que la card use toda la altura disponible
        height: "100%",
        display: "flex",
        flexDirection: "column",
        // Animaciones suaves para reorganización
        transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        transformOrigin: "center",
        "&:hover": {
          transform: "translateY(-2px)",
          boxShadow: (theme) => theme.shadows[8],
        },
      }}
    >
      <CardContent
        sx={{
          p: 1,
          "&:last-child": { pb: 1 },
          // Hacer que el contenido se expanda para usar toda la altura
          height: "100%",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Header con nombre y estado */}
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: 1,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, flex: 1 }}>
            <Typography
              variant="h6"
              sx={{
                fontSize: "0.9rem",
                fontWeight: 600,
                color: (theme) => theme.palette.text.primary,
                transition: "color 0.2s ease-in-out",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                flex: 1,
              }}
            >
              {name}
            </Typography>
            {streamMetrics.isStreaming && streamMetrics.healthScore > 0 && (
              <Tooltip title={`Salud del stream: ${streamMetrics.healthScore}%`}>
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 0.3,
                  }}
                >
                  <HealthIcon
                    sx={{
                      fontSize: "0.9rem",
                      color: streamMetrics.healthScore > 80 
                        ? colorTokens.status.connected 
                        : streamMetrics.healthScore > 60 
                        ? colorTokens.status.connecting 
                        : colorTokens.status.error,
                    }}
                  />
                  <Typography
                    variant="caption"
                    sx={{
                      fontSize: "0.65rem",
                      fontWeight: 600,
                      color: streamMetrics.healthScore > 80 
                        ? colorTokens.status.connected 
                        : streamMetrics.healthScore > 60 
                        ? colorTokens.status.connecting 
                        : colorTokens.status.error,
                    }}
                  >
                    {Math.round(streamMetrics.healthScore)}%
                  </Typography>
                </Box>
              </Tooltip>
            )}
          </Box>
          <Chip
            label={getStatusLabel()}
            size="small"
            icon={<StatusIcon sx={{ fontSize: "0.7rem" }} />}
            sx={{
              backgroundColor: getStatusColor(),
              color: "#ffffff",
              fontSize: "0.7rem",
              fontWeight: 500,
              height: "24px",
              transition: "all 0.2s ease-in-out",
              "&:hover": {
                transform: "scale(1.05)",
              },
            }}
          />
        </Box>

        {/* Información técnica - MOVIDA ARRIBA DEL VIDEO */}
        <Box
          sx={{
            mb: 1,
            p: 0.5,
            backgroundColor: (theme) =>
              theme.palette.mode === "dark"
                ? "rgba(255, 255, 255, 0.05)"
                : "rgba(0, 0, 0, 0.03)",
            borderRadius: "4px",
            border: (theme) => `1px solid ${theme.palette.divider}`,
          }}
        >
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 0.5,
              alignItems: "center",
            }}
          >
            {/* IP */}
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              <NetworkIcon
                sx={{
                  fontSize: "0.8rem",
                  color: (theme) => theme.palette.text.secondary,
                }}
              />
              <Typography
                variant="caption"
                sx={{
                  fontSize: "0.7rem",
                  color: (theme) => theme.palette.text.secondary,
                }}
              >
                {ip}
              </Typography>
            </Box>

            {/* Tiempo conectado */}
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              <TimerIcon
                sx={{
                  fontSize: "0.8rem",
                  color: (theme) => theme.palette.text.secondary,
                }}
              />
              <Typography
                variant="caption"
                sx={{
                  fontSize: "0.7rem",
                  color: (theme) => theme.palette.text.secondary,
                }}
              >
                {displayTime}
              </Typography>
            </Box>

            {/* FPS */}
            <Tooltip 
              title={streamMetrics.avgFps > 0 ? `Promedio: ${streamMetrics.avgFps} FPS` : ""}
              disableHoverListener={!streamMetrics.isStreaming || streamMetrics.avgFps === 0}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                <SpeedIcon
                  sx={{
                    fontSize: "0.8rem",
                    color: (theme) => theme.palette.text.secondary,
                  }}
                />
                <Typography
                  variant="caption"
                  sx={{
                    fontSize: "0.7rem",
                    color: (theme) => theme.palette.text.secondary,
                    cursor: streamMetrics.avgFps > 0 ? "help" : "default",
                  }}
                >
                  {streamMetrics.isStreaming ? `${streamMetrics.fps} FPS` : "-- FPS"}
                </Typography>
              </Box>
            </Tooltip>

            {/* Latencia */}
            <Tooltip 
              title={
                streamMetrics.rtt && streamMetrics.rtt > 0
                  ? `RTT: ${streamMetrics.rtt}ms (Promedio: ${streamMetrics.avgRtt}ms, Min: ${streamMetrics.minRtt}ms, Max: ${streamMetrics.maxRtt}ms)`
                  : streamMetrics.avgLatency > 0
                  ? `Promedio: ${Math.round(streamMetrics.avgLatency)}ms`
                  : ""
              }
              disableHoverListener={!streamMetrics.isStreaming || (streamMetrics.avgLatency === 0 && (!streamMetrics.rtt || streamMetrics.rtt === 0))}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              <NetworkIcon
                sx={{
                  fontSize: "0.8rem",
                  color: (theme) => theme.palette.text.secondary,
                }}
              />
              <Typography
                variant="caption"
                sx={{
                  fontSize: "0.7rem",
                  color: (theme) => theme.palette.text.secondary,
                  display: "flex",
                  alignItems: "baseline",
                  gap: 0.2,
                  cursor: (streamMetrics.avgLatency > 0 || (streamMetrics.rtt && streamMetrics.rtt > 0)) ? "help" : "default",
                }}
              >
                {streamMetrics.isStreaming ? (
                  <>
                    {streamMetrics.rtt && streamMetrics.rtt > 0 ? (
                      // Mostrar RTT real cuando esté disponible
                      <>{streamMetrics.rtt}ms</>
                    ) : (
                      // Mostrar latencia simulada cuando no hay RTT
                      <>
                        {streamMetrics.latency}ms
                        {streamMetrics.latencyType === 'simulated' && (
                          <Typography
                            component="sup"
                            sx={{
                              fontSize: "0.5rem",
                              opacity: 0.7,
                            }}
                          >
                            *
                          </Typography>
                        )}
                      </>
                    )}
                  </>
                ) : (
                  "-- ms"
                )}
              </Typography>
            </Box>
            </Tooltip>
          </Box>
        </Box>

        {/* Área de video con componente VideoPlayer para streaming real - Relación 4:3 */}
        <Box
          sx={{
            position: "relative",
            width: "100%",
            // Mantener relación de aspecto 16:9
            aspectRatio: "16/9",
            backgroundColor: "#000",
            borderRadius: "6px",
            overflow: "hidden",
            mb: 1,
            // Flex para que ocupe el espacio disponible
            flex: "1 1 auto",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <VideoStream
            cameraId={cameraId}
            isConnected={isConnected}
            aspectRatio="16/9"
            height="100%"
            onError={useCallback(
              (error: any) => console.error(`Error en cámara ${cameraId}:`, error),
              [cameraId]
            )}
            onMetricsUpdate={useCallback(
              (metrics: any) => {
                if (isConnected) {
                  // Solo logear cambios significativos (cada 10 frames)
                  if (metrics.fps && Math.floor(metrics.fps * 10) % 100 === 0) {
                    console.log(`[CameraCard ${cameraId}] Métricas actualizadas:`, metrics);
                  }
                  setStreamMetrics(metrics);
                }
              },
              [isConnected, cameraId]
            )}
          />
        </Box>

        {/* Botones de acción - REBALANCEADOS A 1/3 CADA UNO */}
        <Box
          sx={{
            mt: 1,
            display: "flex",
            gap: 0.5,
            width: "100%",
          }}
        >
          {/* Botón Conectar/Desconectar - 1/3 del ancho */}
          <Button
            variant={isConnected ? "outlined" : "contained"}
            size="small"
            startIcon={isConnected ? <DisconnectIcon /> : <ConnectIcon />}
            onClick={isConnected ? onDisconnect : onConnect}
            disabled={isConnecting}
            sx={{
              flex: "1", // 1/3 del ancho disponible
              fontSize: "0.65rem",
              height: "28px",
              borderRadius: "4px",
              transition: "all 0.2s ease-in-out",
              minWidth: 0, // Permitir que se comprima
              ...(isConnected
                ? {
                    color: colorTokens.status.error,
                    borderColor: colorTokens.status.error,
                    "&:hover": {
                      backgroundColor: colorTokens.status.error,
                      color: "#ffffff",
                    },
                  }
                : {
                    backgroundColor: colorTokens.status.connected,
                    "&:hover": {
                      backgroundColor: colorTokens.status.connected,
                      filter: "brightness(1.1)",
                    },
                  }),
            }}
          >
            {isConnecting
              ? "Conectando..."
              : isConnected
              ? "Desconectar"
              : "Conectar"}
          </Button>

          {/* Botón Configuración - 1/3 del ancho */}
          <Button
            variant="outlined"
            size="small"
            startIcon={<SettingsIcon />}
            onClick={onSettings}
            sx={{
              flex: "1", // 1/3 del ancho disponible
              fontSize: "0.65rem",
              height: "28px",
              borderRadius: "4px",
              transition: "all 0.2s ease-in-out",
              minWidth: 0, // Permitir que se comprima
              color: (theme) => theme.palette.text.secondary,
              borderColor: (theme) => theme.palette.divider,
              "&:hover": {
                color: (theme) => theme.palette.primary.main,
                borderColor: (theme) => theme.palette.primary.main,
                backgroundColor: (theme) => theme.palette.action.hover,
              },
            }}
          >
            Config
          </Button>

          {/* Botón Capturar - 1/3 del ancho */}
          <Button
            variant="outlined"
            size="small"
            startIcon={<CameraAltIcon />}
            onClick={onCapture}
            disabled={!isConnected}
            sx={{
              flex: "1", // 1/3 del ancho disponible
              fontSize: "0.65rem",
              height: "28px",
              borderRadius: "4px",
              transition: "all 0.2s ease-in-out",
              minWidth: 0, // Permitir que se comprima
              color: (theme) => theme.palette.text.secondary,
              borderColor: (theme) => theme.palette.divider,
              "&:hover": {
                color: (theme) => theme.palette.primary.main,
                borderColor: (theme) => theme.palette.primary.main,
                backgroundColor: (theme) => theme.palette.action.hover,
              },
              "&.Mui-disabled": {
                color: (theme) => theme.palette.text.disabled,
                borderColor: (theme) => theme.palette.divider,
              },
            }}
          >
            Captura
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
});

// Añadir displayName para debugging
CameraCard.displayName = 'CameraCard';
