/**
 * 🎯 Camera Grid Component - Universal Camera Viewer
 * Grilla responsiva para mostrar múltiples cámaras
 */

import { memo, useMemo } from "react";
import { Box, Typography, Fade, Grow, CircularProgress } from "@mui/material";
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
  // Si no hay cámaras, mostrar estado vacío con animación
  if (cameras.length === 0 && !isLoading) {
    return (
      <Fade in timeout={800}>
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
          <Grow in timeout={600} style={{ transitionDelay: '200ms' }}>
            <VideocamIcon
              sx={{
                fontSize: 80,
                color: (theme) => theme.palette.text.disabled,
                mb: 2,
              }}
            />
          </Grow>
          <Fade in timeout={600} style={{ transitionDelay: '400ms' }}>
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
          </Fade>
          <Fade in timeout={600} style={{ transitionDelay: '600ms' }}>
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
          </Fade>
        </Box>
      </Fade>
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
        // Estado de carga mejorado
        <Fade in timeout={300}>
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: gridTemplateColumns,
              gap: 0.5,
              width: "100%",
              transition: "grid-template-columns 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
            }}
          >
            {/* Mostrar skeletons de carga con animación mejorada */}
            {Array.from({ length: 6 }).map((_, index) => (
              <Grow
                key={`skeleton-${index}`}
                in
                timeout={600}
                style={{ 
                  transitionDelay: `${index * 100}ms`,
                  transformOrigin: '0 0 0' 
                }}
              >
                <Box
                  sx={{
                    height: "300px",
                    backgroundColor: (theme) =>
                      theme.palette.mode === "dark"
                        ? colorTokens.background.darkElevated
                        : colorTokens.background.lightElevated,
                    borderRadius: "4px",
                    border: (theme) => `1px solid ${theme.palette.divider}`,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 2,
                    position: "relative",
                    overflow: "hidden",
                    "&::after": {
                      content: '""',
                      position: "absolute",
                      top: 0,
                      left: "-100%",
                      width: "100%",
                      height: "100%",
                      background: (theme) =>
                        `linear-gradient(90deg, transparent, ${
                          theme.palette.mode === "dark"
                            ? "rgba(255, 255, 255, 0.05)"
                            : "rgba(0, 0, 0, 0.03)"
                        }, transparent)`,
                      animation: "shimmer 2s infinite",
                    },
                    "@keyframes shimmer": {
                      "0%": { left: "-100%" },
                      "100%": { left: "100%" },
                    },
                  }}
                >
                  <CircularProgress
                    size={24}
                    thickness={2}
                    sx={{
                      color: (theme) => theme.palette.text.disabled,
                      opacity: 0.6,
                    }}
                  />
                  <Typography
                    variant="caption"
                    sx={{ 
                      color: (theme) => theme.palette.text.disabled,
                      opacity: 0.8,
                    }}
                  >
                    Cargando cámara...
                  </Typography>
                </Box>
              </Grow>
            ))}
          </Box>
        </Fade>
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
            <Grow
              key={camera.id}
              in
              timeout={800}
              style={{ 
                transitionDelay: `${Math.min(index * 50, 300)}ms`,
                transformOrigin: 'center center'
              }}
            >
              <Box
                sx={{
                  // Asegurar que el wrapper ocupe toda la altura disponible
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
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
            </Grow>
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
