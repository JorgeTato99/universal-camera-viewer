/**
 * 🎯 Cameras Page - Universal Camera Viewer
 * Página principal de gestión de cámaras con nuevo design system
 */

import React, { useState } from "react";
import { Box, Typography } from "@mui/material";
import { CameraToolbar, CameraGrid } from "./components";
import { useCameraStore } from "../../stores";

const CamerasPage: React.FC = () => {
  const { cameras, isLoading } = useCameraStore();
  const [gridColumns, setGridColumns] = useState<2 | 3>(3);
  const [isChangingLayout, setIsChangingLayout] = useState(false);

  // Datos simulados para demostrar el layout con información técnica completa
  const mockCameras = [
    {
      id: "cam-001",
      name: "Cámara Entrada",
      status: "connected" as const,
      ip: "192.168.1.101",
      fps: 30,
      latency: 25,
      connectedTime: "02:30:15",
      aspectRatio: "16:9" as const,
    },
    {
      id: "cam-002",
      name: "Cámara Sala",
      status: "disconnected" as const,
      ip: "192.168.1.102",
      fps: 0,
      latency: 0,
      connectedTime: "00:00:00",
      aspectRatio: "16:9" as const,
    },
    {
      id: "cam-003",
      name: "Cámara Cocina",
      status: "connecting" as const,
      ip: "192.168.1.103",
      fps: 0,
      latency: 0,
      connectedTime: "00:00:00",
      aspectRatio: "4:3" as const,
    },
    {
      id: "cam-004",
      name: "Cámara Jardín",
      status: "error" as const,
      ip: "192.168.1.104",
      fps: 0,
      latency: 0,
      connectedTime: "00:00:00",
      aspectRatio: "16:9" as const,
    },
    {
      id: "cam-005",
      name: "Cámara Garaje",
      status: "connected" as const,
      ip: "192.168.1.105",
      fps: 25,
      latency: 40,
      connectedTime: "01:15:30",
      aspectRatio: "16:9" as const,
    },
    {
      id: "cam-006",
      name: "Cámara Oficina",
      status: "connected" as const,
      ip: "192.168.1.106",
      fps: 30,
      latency: 18,
      connectedTime: "00:45:20",
      aspectRatio: "4:3" as const,
    },
  ];

  // Calcular cámaras conectadas
  const connectedCameras = mockCameras.filter(
    (camera) => camera.status === "connected"
  ).length;

  const handleGridColumnsChange = (columns: 2 | 3) => {
    setIsChangingLayout(true);
    setGridColumns(columns);

    // Resetear el estado después de la animación
    setTimeout(() => {
      setIsChangingLayout(false);
    }, 400); // Coincide con la duración de la transición del grid
  };

  const handleConnectAll = () => {
    console.log("Conectar todas las cámaras");
    // TODO: Implementar lógica de conexión
  };

  const handleDisconnectAll = () => {
    console.log("Desconectar todas las cámaras");
    // TODO: Implementar lógica de desconexión
  };

  // Handlers para acciones de cámaras individuales
  const handleCameraConnect = (cameraId: string) => {
    console.log(`Conectar cámara: ${cameraId}`);
    // TODO: Implementar lógica de conexión individual
  };

  const handleCameraDisconnect = (cameraId: string) => {
    console.log(`Desconectar cámara: ${cameraId}`);
    // TODO: Implementar lógica de desconexión individual
  };

  const handleCameraSettings = (cameraId: string) => {
    console.log(`Abrir configuración de cámara: ${cameraId}`);
    // TODO: Implementar modal de configuración
  };

  const handleCameraCapture = (cameraId: string) => {
    console.log(`Capturar imagen de cámara: ${cameraId}`);
    // TODO: Implementar captura de imagen
  };

  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      {/* Toolbar superior */}
      <CameraToolbar
        connectedCameras={connectedCameras}
        totalCameras={mockCameras.length}
        gridColumns={gridColumns}
        onGridColumnsChange={handleGridColumnsChange}
        onConnectAll={handleConnectAll}
        onDisconnectAll={handleDisconnectAll}
      />

      {/* Grid de cámaras */}
      <Box
        sx={{
          flex: 1,
          overflow: "auto",
          // Eliminar padding extra y optimizar espacio
          p: 0,
          m: 0,
          position: "relative",
        }}
      >
        {/* Indicador de reorganización */}
        {isChangingLayout && (
          <Box
            sx={{
              position: "absolute",
              top: 8,
              right: 8,
              zIndex: 10,
              backgroundColor: (theme) => theme.palette.background.paper,
              borderRadius: "8px",
              padding: "4px 8px",
              border: (theme) => `1px solid ${theme.palette.divider}`,
              boxShadow: (theme) => theme.shadows[2],
              display: "flex",
              alignItems: "center",
              gap: 1,
              opacity: 0,
              animation: "fadeInOut 0.4s ease-in-out",
              "@keyframes fadeInOut": {
                "0%": { opacity: 0, transform: "translateY(-10px)" },
                "50%": { opacity: 1, transform: "translateY(0)" },
                "100%": { opacity: 0, transform: "translateY(-10px)" },
              },
            }}
          >
            <Typography
              variant="caption"
              sx={{
                color: (theme) => theme.palette.text.secondary,
                fontSize: "0.7rem",
                fontWeight: 500,
              }}
            >
              Reorganizando...
            </Typography>
          </Box>
        )}

        <CameraGrid
          cameras={mockCameras}
          gridColumns={gridColumns}
          isLoading={isLoading}
          onCameraConnect={handleCameraConnect}
          onCameraDisconnect={handleCameraDisconnect}
          onCameraSettings={handleCameraSettings}
          onCameraCapture={handleCameraCapture}
        />
      </Box>
    </Box>
  );
};

export default CamerasPage;
