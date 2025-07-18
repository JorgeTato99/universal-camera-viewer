/**
 * 🎯 Camera Grid Component - Universal Camera Viewer
 * Grilla responsiva para mostrar múltiples cámaras
 */

import React, { memo, useMemo } from "react";
import { Box, Typography } from "@mui/material";
import { Videocam as VideocamIcon } from "@mui/icons-material";
import { CameraCard } from "./CameraCard";
import { colorTokens } from "../../../design-system/tokens";

interface Camera {
  id: string;
  name: string;
  status: "connected" | "disconnected" | "connecting" | "error";
  aspectRatio?: "16:9" | "4:3";
  ip?: string;
  fps?: number;
  latency?: number;
  connectedTime?: string;
}

interface CameraGridProps {
  cameras: Camera[];
  gridColumns: 2 | 3 | 4 | 5;
  isLoading?: boolean;
  onCameraConnect?: (cameraId: string) => void;
  onCameraDisconnect?: (cameraId: string) => void;
  onCameraSettings?: (cameraId: string) => void;
  onCameraCapture?: (cameraId: string) => void;
}

// Componente optimizado con memo para evitar re-renders innecesarios
export const CameraGrid = memo<CameraGridProps>(({
  cameras,
  gridColumns,
  isLoading = false,
  onCameraConnect,
  onCameraDisconnect,
  onCameraSettings,
  onCameraCapture,
}) => {
  // Si no hay cámaras, mostrar estado vacío
  if (cameras.length === 0 && !isLoading) {
    return (
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "400px",
          textAlign: "center",
          p: 4,
        }}
      >
        <VideocamIcon
          sx={{
            fontSize: 80,
            color: (theme) => theme.palette.text.disabled,
            mb: 2,
          }}
        />
        <Typography
          variant="h5"
          sx={{
            mb: 1,
            color: (theme) => theme.palette.text.secondary,
            fontWeight: 500,
          }}
        >
          No hay cámaras configuradas
        </Typography>
        <Typography
          variant="body2"
          sx={{
            color: (theme) => theme.palette.text.secondary,
            maxWidth: "400px",
          }}
        >
          Agrega cámaras para comenzar a monitorear tus espacios. Puedes
          configurar cámaras IP, USB o de red.
        </Typography>
      </Box>
    );
  }

  // Configurar el número de columnas según la selección con memoización
  const gridTemplateColumns = useMemo(() => {
    // Ajustes responsivos mejorados para diferentes tamaños de pantalla
    const responsiveColumns = {
      xs: 1, // Móviles siempre 1 columna
      sm: Math.min(2, gridColumns), // Tablets máximo 2 columnas
      md: Math.min(3, gridColumns), // Pantallas medianas máximo 3
      lg: Math.min(4, gridColumns), // Pantallas grandes máximo 4
      xl: gridColumns, // Pantallas XL usan el valor completo
    };

    return {
      xs: "1fr",
      sm: `repeat(${responsiveColumns.sm}, 1fr)`,
      md: `repeat(${responsiveColumns.md}, 1fr)`,
      lg: `repeat(${responsiveColumns.lg}, 1fr)`,
      xl: `repeat(${responsiveColumns.xl}, 1fr)`,
    };
  }, [gridColumns]);

  return (
    <Box
      sx={{
        p: 0.5, // Reducido de 3 a 0.5 para márgenes mínimos
        backgroundColor: (theme) => theme.palette.background.default,
      }}
    >
      {isLoading ? (
        // Estado de carga
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: gridTemplateColumns,
            gap: 0.5, // Reducido de 3 a 0.5 para espaciado mínimo
            width: "100%",
            // Transición suave para cambio de layout
            transition:
              "grid-template-columns 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
          }}
        >
          {/* Mostrar skeletons de carga */}
          {Array.from({ length: 6 }).map((_, index) => (
            <Box
              key={`skeleton-${index}`}
              sx={{
                height: "300px",
                backgroundColor: (theme) =>
                  theme.palette.mode === "dark"
                    ? colorTokens.background.darkElevated
                    : colorTokens.background.lightElevated,
                borderRadius: "4px",
                border: (theme) => `1px solid ${theme.palette.divider}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                animation: "pulse 1.5s ease-in-out infinite",
                // Animación de entrada para skeletons
                opacity: 0,
                animationDelay: `${index * 0.1}s`,
                animationFillMode: "forwards",
                "@keyframes pulse": {
                  "0%": {
                    opacity: 0,
                  },
                  "50%": {
                    opacity: 0.5,
                  },
                  "100%": {
                    opacity: 1,
                  },
                },
              }}
            >
              <Typography
                variant="body2"
                sx={{ color: (theme) => theme.palette.text.disabled }}
              >
                Cargando...
              </Typography>
            </Box>
          ))}
        </Box>
      ) : (
        // Grilla de cámaras
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: gridTemplateColumns,
            gap: 0.5, // Reducido de 3 a 0.5 para espaciado mínimo
            width: "100%",
            // Transición suave para cambio de layout
            transition:
              "grid-template-columns 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
            // Asegurar que las cards mantengan un aspect ratio consistente
            "& > *": {
              minHeight: "280px",
              height: "100%", // Asegurar que el wrapper use toda la altura
              display: "flex", // Para que la card interna se expanda
              flexDirection: "column",
              // Animación para las cards individuales
              transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
              transformOrigin: "center",
              "&:hover": {
                transform: "scale(1.02)",
                zIndex: 1,
              },
            },
          }}
        >
          {cameras.map((camera, index) => (
            <Box
              key={camera.id}
              sx={{
                // Animación de entrada escalonada
                animation: "slideInUp 0.5s ease-out",
                animationDelay: `${index * 0.1}s`,
                animationFillMode: "both",
                // Asegurar que el wrapper ocupe toda la altura disponible
                height: "100%",
                display: "flex",
                flexDirection: "column",
                "@keyframes slideInUp": {
                  "0%": {
                    opacity: 0,
                    transform: "translateY(20px)",
                  },
                  "100%": {
                    opacity: 1,
                    transform: "translateY(0)",
                  },
                },
              }}
            >
              <CameraCard
                cameraId={camera.id}
                name={camera.name}
                status={camera.status}
                aspectRatio={camera.aspectRatio}
                ip={camera.ip}
                fps={camera.fps}
                latency={camera.latency}
                connectedTime={camera.connectedTime}
                onConnect={() => onCameraConnect?.(camera.id)}
                onDisconnect={() => onCameraDisconnect?.(camera.id)}
                onSettings={() => onCameraSettings?.(camera.id)}
                onCapture={() => onCameraCapture?.(camera.id)}
              />
            </Box>
          ))}
        </Box>
      )}

      {/* Información adicional en la parte inferior */}
      {cameras.length > 0 && !isLoading && (
        <Box
          sx={{
            mt: 0.5, // Reducido de 3 a 0.5 para espaciado mínimo
            pt: 1, // Reducido de 2 a 1
            borderTop: (theme) => `1px solid ${theme.palette.divider}`,
            display: "flex",
            justifyContent: "center",
            // Animación para la información del footer
            opacity: 0,
            animation: "fadeIn 0.6s ease-out 0.4s",
            animationFillMode: "forwards",
            "@keyframes fadeIn": {
              "0%": {
                opacity: 0,
                transform: "translateY(10px)",
              },
              "100%": {
                opacity: 1,
                transform: "translateY(0)",
              },
            },
          }}
        >
          <Typography
            variant="caption"
            sx={{ color: (theme) => theme.palette.text.secondary }}
          >
            Mostrando {cameras.length} cámara{cameras.length !== 1 ? "s" : ""}{" "}
            en {gridColumns} columnas
          </Typography>
        </Box>
      )}
    </Box>
  );
});

// Añadir displayName para debugging
CameraGrid.displayName = 'CameraGrid';
