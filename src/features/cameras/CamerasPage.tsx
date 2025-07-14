/**
 * 🎯 Cameras Page - Universal Camera Viewer
 * Página principal de gestión de cámaras con nuevo design system
 */

import React, { useState } from "react";
import { Box } from "@mui/material";
import { CameraToolbar, CameraGrid } from "./components";
import { useCameraStore } from "../../stores";

const CamerasPage: React.FC = () => {
  const { cameras, isLoading } = useCameraStore();
  const [gridColumns, setGridColumns] = useState<2 | 3>(3);

  // Datos simulados para demostrar el layout
  const mockCameras = [
    { id: "cam-001", name: "Cámara Entrada", status: "connected" as const },
    { id: "cam-002", name: "Cámara Sala", status: "disconnected" as const },
    { id: "cam-003", name: "Cámara Cocina", status: "connecting" as const },
    { id: "cam-004", name: "Cámara Jardín", status: "error" as const },
    { id: "cam-005", name: "Cámara Garaje", status: "connected" as const },
    { id: "cam-006", name: "Cámara Oficina", status: "disconnected" as const },
  ];

  // Calcular cámaras conectadas
  const connectedCameras = mockCameras.filter(
    (camera) => camera.status === "connected"
  ).length;

  const handleGridColumnsChange = (columns: 2 | 3) => {
    setGridColumns(columns);
  };

  const handleConnectAll = () => {
    console.log("Conectar todas las cámaras");
    // TODO: Implementar lógica de conexión
  };

  const handleDisconnectAll = () => {
    console.log("Desconectar todas las cámaras");
    // TODO: Implementar lógica de desconexión
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
        }}
      >
        <CameraGrid
          cameras={mockCameras}
          gridColumns={gridColumns}
          isLoading={isLoading}
        />
      </Box>
    </Box>
  );
};

export default CamerasPage;
