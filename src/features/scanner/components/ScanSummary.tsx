/**
 * 🎯 Scan Summary Component - Universal Camera Viewer
 * Resumen del estado del escaneo
 */

import React from "react";
import {
  Box,
  Typography,
  Paper,
  LinearProgress,
  Chip,
  alpha,
  Fade,
  keyframes,
} from "@mui/material";
import {
  DevicesOther as DevicesIcon,
  Videocam as CameraIcon,
  CheckCircle as CompleteIcon,
  Pending as PendingIcon,
  NetworkCheck as NetworkIcon,
} from "@mui/icons-material";
import { colorTokens, borderTokens } from "../../../design-system/tokens";

// Animación de rotación para el icono
const rotateAnimation = keyframes`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`;

// Animación de pulso
const pulseAnimation = keyframes`
  0% {
    box-shadow: 0 0 0 0 rgba(33, 150, 243, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(33, 150, 243, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(33, 150, 243, 0);
  }
`;

interface ScanSummaryProps {
  totalDevices: number;
  possibleCameras: number;
  activeStep: number;
  scanProgress?: number;
}

export const ScanSummary: React.FC<ScanSummaryProps> = ({
  totalDevices,
  possibleCameras,
  activeStep,
  scanProgress = 0,
}) => {
  const getStepStatus = () => {
    switch (activeStep) {
      case 0:
        return {
          icon: <NetworkIcon />,
          title: "Escaneo de Red",
          status: scanProgress > 0 ? "En progreso" : "Preparado",
          color: colorTokens.primary[500],
        };
      case 1:
        return {
          icon: <DevicesIcon />,
          title: "Análisis de Puertos",
          status: "En progreso",
          color: colorTokens.status.connecting,
        };
      case 2:
        return {
          icon: <CameraIcon />,
          title: "Verificación de Acceso",
          status: "En progreso",
          color: colorTokens.status.connected,
        };
      default:
        return {
          icon: <NetworkIcon />,
          title: "Listo para escanear",
          status: "Inactivo",
          color: colorTokens.neutral[500],
        };
    }
  };

  const stepInfo = getStepStatus();

  return (
    <Box>
      {/* Estado actual */}
      <Fade in timeout={500}>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 2,
            mb: 2,
          }}
        >
          <Box
            sx={{
              width: 40,
              height: 40,
              borderRadius: "50%",
              backgroundColor: alpha(stepInfo.color, 0.1),
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: stepInfo.color,
              transition: "all 0.3s ease",
              animation: scanProgress > 0 && scanProgress < 100
                ? `${pulseAnimation} 2s infinite`
                : "none",
              "& svg": {
                animation: scanProgress > 0 && scanProgress < 100
                  ? `${rotateAnimation} 3s linear infinite`
                  : "none",
              },
            }}
          >
            {stepInfo.icon}
          </Box>
        <Box sx={{ flex: 1 }}>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {stepInfo.title}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {stepInfo.status}
          </Typography>
        </Box>
        </Box>
      </Fade>

      {/* Progreso si está escaneando */}
      {scanProgress > 0 && activeStep === 0 && (
        <Box sx={{ mb: 2 }}>
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              mb: 0.5,
            }}
          >
            <Typography variant="caption" color="text.secondary">
              Progreso del escaneo
            </Typography>
            <Typography
              variant="caption"
              sx={{ fontWeight: 600, color: colorTokens.primary[500] }}
            >
              {scanProgress}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={scanProgress}
            sx={{
              height: 4,
              borderRadius: 2,
              backgroundColor: (theme) =>
                theme.palette.mode === "dark"
                  ? alpha(colorTokens.primary[500], 0.2)
                  : colorTokens.primary[100],
              "& .MuiLinearProgress-bar": {
                borderRadius: 2,
                backgroundColor: colorTokens.primary[500],
              },
            }}
          />
        </Box>
      )}

      {/* Estadísticas */}
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 1.5,
        }}
      >
        {/* Total de dispositivos */}
        <Paper
          variant="outlined"
          sx={{
            p: 1.5,
            textAlign: "center",
            border: (theme) =>
              `1px solid ${alpha(theme.palette.divider, 0.5)}`,
            backgroundColor: (theme) =>
              theme.palette.mode === "dark"
                ? "rgba(255, 255, 255, 0.02)"
                : "rgba(0, 0, 0, 0.01)",
          }}
        >
          <Typography
            variant="h6"
            sx={{
              fontWeight: 600,
              color: (theme) => theme.palette.text.primary,
            }}
          >
            {totalDevices}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Dispositivos totales
          </Typography>
        </Paper>

        {/* Posibles cámaras */}
        <Fade in timeout={700}>
          <Paper
            variant="outlined"
            sx={{
              p: 1.5,
              textAlign: "center",
              border: (theme) =>
                `1px solid ${
                  possibleCameras > 0
                    ? alpha(colorTokens.status.connected, 0.3)
                    : alpha(theme.palette.divider, 0.5)
                }`,
              backgroundColor:
                possibleCameras > 0
                  ? alpha(colorTokens.status.connected, 0.05)
                  : (theme) =>
                      theme.palette.mode === "dark"
                        ? "rgba(255, 255, 255, 0.02)"
                        : "rgba(0, 0, 0, 0.01)",
              borderRadius: borderTokens.radius.md,
              transition: "all 0.3s ease",
              cursor: "default",
              "&:hover": {
                borderColor: possibleCameras > 0
                  ? colorTokens.status.connected
                  : colorTokens.primary[200],
                backgroundColor: possibleCameras > 0
                  ? alpha(colorTokens.status.connected, 0.08)
                  : (theme) =>
                      theme.palette.mode === "dark"
                        ? "rgba(255, 255, 255, 0.04)"
                        : "rgba(0, 0, 0, 0.02)",
                transform: "translateY(-2px)",
                boxShadow: theme => theme.shadows[2],
              },
            }}
          >
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                color:
                  possibleCameras > 0
                    ? colorTokens.status.connected
                    : (theme) => theme.palette.text.primary,
                transition: "color 0.3s ease",
              }}
            >
              {possibleCameras}
            </Typography>
            <Typography
              variant="caption"
              sx={{
                color:
                  possibleCameras > 0
                    ? colorTokens.status.connected
                    : "text.secondary",
              }}
            >
              Posibles cámaras
            </Typography>
          </Paper>
        </Fade>
      </Box>

      {/* Indicadores de estado */}
      <Box sx={{ mt: 2 }}>
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ fontWeight: 500 }}
        >
          Estados:
        </Typography>
        <Box
          sx={{
            display: "flex",
            gap: 0.5,
            mt: 0.5,
            flexWrap: "wrap",
          }}
        >
          <Chip
            icon={<CompleteIcon sx={{ fontSize: 14 }} />}
            label="Completados"
            size="small"
            sx={{
              height: 20,
              fontSize: "0.65rem",
              "& .MuiChip-icon": {
                marginLeft: "4px",
                color: colorTokens.status.connected,
              },
            }}
          />
          <Chip
            icon={<PendingIcon sx={{ fontSize: 14 }} />}
            label="Pendientes"
            size="small"
            sx={{
              height: 20,
              fontSize: "0.65rem",
              "& .MuiChip-icon": {
                marginLeft: "4px",
                color: colorTokens.status.connecting,
              },
            }}
          />
        </Box>
      </Box>

      {/* Sugerencia contextual */}
      {possibleCameras > 0 && activeStep === 0 && (
        <Box
          sx={{
            mt: 2,
            p: 1,
            backgroundColor: alpha(colorTokens.status.connected, 0.1),
            borderRadius: 1,
            border: `1px solid ${alpha(colorTokens.status.connected, 0.3)}`,
          }}
        >
          <Typography
            variant="caption"
            sx={{
              color: colorTokens.status.connected,
              fontWeight: 500,
            }}
          >
            ¡{possibleCameras} dispositivo(s) con alta probabilidad de ser
            cámara(s)!
          </Typography>
        </Box>
      )}
    </Box>
  );
};