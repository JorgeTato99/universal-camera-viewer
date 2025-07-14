/**
 * 🎯 Camera Card Component - Universal Camera Viewer
 * Card individual para cada cámara con información completa
 */

import React from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  Button,
  IconButton,
  Divider,
  Tooltip,
} from "@mui/material";
import {
  Videocam as VideocamIcon,
  Settings as SettingsIcon,
  CameraAlt as CameraAltIcon,
  PowerSettingsNew as ConnectIcon,
  PowerOff as DisconnectIcon,
  Circle as StatusIcon,
  NetworkCheck as NetworkIcon,
  Timer as TimerIcon,
  Speed as SpeedIcon,
} from "@mui/icons-material";
import { cardStyles, statusStyles } from "../../../design-system/components";
import { colorTokens } from "../../../design-system/tokens";

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

export const CameraCard: React.FC<CameraCardProps> = ({
  cameraId,
  name = `Cámara ${cameraId}`,
  status = "disconnected",
  aspectRatio = "16:9",
  ip = "192.168.1.100",
  fps = 30,
  latency = 45,
  connectedTime = "02:30:15",
  onConnect,
  onDisconnect,
  onSettings,
  onCapture,
}) => {
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

  const isConnected = status === "connected";
  const isConnecting = status === "connecting";

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
              maxWidth: "60%",
            }}
          >
            {name}
          </Typography>
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
                {isConnected ? connectedTime : "--:--:--"}
              </Typography>
            </Box>

            {/* FPS */}
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
                }}
              >
                {isConnected ? `${fps} FPS` : "-- FPS"}
              </Typography>
            </Box>

            {/* Latencia */}
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
                {isConnected ? `${latency}ms` : "-- ms"}
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Área de video placeholder - SIN OVERLAY */}
        <Box
          sx={{
            width: "100%",
            flex: 1, // Usar flex: 1 para que ocupe el espacio disponible
            aspectRatio: aspectRatio,
            backgroundColor: (theme) =>
              theme.palette.mode === "dark"
                ? colorTokens.background.dark
                : colorTokens.background.light,
            borderRadius: "6px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            border: (theme) => `1px solid ${theme.palette.divider}`,
            position: "relative",
            overflow: "hidden",
            transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
            "&:hover": {
              borderColor: (theme) => theme.palette.primary.main,
            },
          }}
        >
          {isConnected ? (
            // Placeholder para video en vivo
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 0.5,
                color: (theme) => theme.palette.text.secondary,
                transition: "all 0.2s ease-in-out",
              }}
            >
              <VideocamIcon
                sx={{
                  fontSize: 32,
                  color: colorTokens.status.connected,
                  transition: "all 0.2s ease-in-out",
                  "&:hover": {
                    transform: "scale(1.1)",
                  },
                }}
              />
              <Typography variant="caption" sx={{ fontSize: "0.7rem" }}>
                Video en vivo
              </Typography>
            </Box>
          ) : (
            // Placeholder para cámara desconectada
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 0.5,
                color: (theme) => theme.palette.text.disabled,
                transition: "all 0.2s ease-in-out",
              }}
            >
              <VideocamIcon
                sx={{
                  fontSize: 32,
                  transition: "all 0.2s ease-in-out",
                  "&:hover": {
                    transform: "scale(1.1)",
                  },
                }}
              />
              <Typography variant="caption" sx={{ fontSize: "0.7rem" }}>
                Sin conexión
              </Typography>
            </Box>
          )}
        </Box>

        {/* Botones de acción - REBALANCEADOS */}
        <Box
          sx={{
            mt: 1,
            display: "flex",
            gap: 0.5,
            justifyContent: "space-between",
          }}
        >
          {/* Botón principal (Conectar/Desconectar) - 65% del ancho */}
          <Button
            variant={isConnected ? "outlined" : "contained"}
            size="small"
            startIcon={isConnected ? <DisconnectIcon /> : <ConnectIcon />}
            onClick={isConnected ? onDisconnect : onConnect}
            disabled={isConnecting}
            sx={{
              flex: "0 0 65%", // 65% del ancho disponible
              fontSize: "0.7rem",
              height: "28px",
              borderRadius: "4px",
              transition: "all 0.2s ease-in-out",
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

          {/* Botones secundarios - 35% del ancho restante */}
          <Box
            sx={{
              display: "flex",
              gap: 0.5,
              flex: "0 0 35%", // 35% del ancho restante
              justifyContent: "space-between",
            }}
          >
            <Tooltip title="Configuración">
              <IconButton
                size="small"
                onClick={onSettings}
                sx={{
                  flex: 1, // Repartir equitativamente el espacio
                  height: "28px",
                  color: (theme) => theme.palette.text.secondary,
                  transition: "all 0.2s ease-in-out",
                  "&:hover": {
                    color: (theme) => theme.palette.primary.main,
                    backgroundColor: (theme) => theme.palette.action.hover,
                  },
                }}
              >
                <SettingsIcon sx={{ fontSize: "0.9rem" }} />
              </IconButton>
            </Tooltip>

            <Tooltip title="Capturar">
              <IconButton
                size="small"
                onClick={onCapture}
                disabled={!isConnected}
                sx={{
                  flex: 1, // Repartir equitativamente el espacio
                  height: "28px",
                  color: (theme) => theme.palette.text.secondary,
                  transition: "all 0.2s ease-in-out",
                  "&:hover": {
                    color: (theme) => theme.palette.primary.main,
                    backgroundColor: (theme) => theme.palette.action.hover,
                  },
                  "&.Mui-disabled": {
                    color: (theme) => theme.palette.text.disabled,
                  },
                }}
              >
                <CameraAltIcon sx={{ fontSize: "0.9rem" }} />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};
