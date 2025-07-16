/**
 * 🎯 Cameras Page - Universal Camera Viewer
 * Página principal de gestión de cámaras con nuevo design system
 */

import React, { useState, useEffect } from "react";
import { Box, Typography } from "@mui/material";
import { CameraToolbar, CameraGrid } from "./components";
import { useCameraStoreV2 } from "../../stores/cameraStore.v2";
import { cameraServiceV2 } from "../../services/python/cameraService.v2";
import { streamingService } from "../../services/python/streamingService";
import { useNotificationStore } from "../../stores/notificationStore";
import { CameraResponse, ConnectionStatus } from "../../types/camera.types.v2";

// Ya no necesitamos convertir, usamos directamente CameraResponse

const CamerasPage: React.FC = () => {
  const { 
    cameras, 
    isLoading, 
    loadCameras,
    connectCamera,
    disconnectCamera,
    getFilteredCameras,
    getCameraStats,
    gridColumns,
    setGridColumns,
  } = useCameraStoreV2();
  const { addNotification } = useNotificationStore();
  const [isChangingLayout, setIsChangingLayout] = useState(false);

  // Cargar cámaras desde el backend
  useEffect(() => {
    loadCameras();
  }, [loadCameras]);

  // Obtener cámaras filtradas del store
  const filteredCameras = getFilteredCameras();
  console.log('Cámaras filtradas del store:', filteredCameras);
  console.log('Total cámaras en store:', cameras.size);
  
  // Transformar datos de cámaras para el componente
  const cameraData = filteredCameras.map((camera) => ({
    id: camera.camera_id,
    name: camera.display_name || `Cámara ${camera.camera_id}`,
    status: camera.is_connected ? 'connected' as const : 'disconnected' as const,
    ip: camera.ip_address,
    fps: camera.is_connected ? 30 : 0, // Mock FPS por ahora
    latency: camera.is_connected ? 45 : 0, // Mock latency por ahora
    connectedTime: camera.is_connected ? "02:30:15" : "00:00:00", // Mock por ahora
    aspectRatio: "16:9" as const,
  }));
  console.log('Datos de cámaras transformados:', cameraData);

  // Obtener estadísticas de cámaras
  const cameraStats = getCameraStats();
  const connectedCameras = cameraStats.connected;

  const handleGridColumnsChange = (columns: 2 | 3) => {
    setIsChangingLayout(true);
    setGridColumns(columns);

    // Resetear el estado después de la animación
    setTimeout(() => {
      setIsChangingLayout(false);
    }, 400); // Coincide con la duración de la transición del grid
  };

  const handleConnectAll = async () => {
    await connectAllCameras();
  };

  const handleDisconnectAll = async () => {
    await disconnectAllCameras();
  };

  // Handlers para acciones de cámaras individuales
  const handleCameraConnect = async (cameraId: string) => {
    await connectCamera(cameraId);
  };

  const handleCameraDisconnect = async (cameraId: string) => {
    try {
      // Primero detener el streaming WebSocket si está activo
      if (streamingService.isConnected() && streamingService.cameraId === cameraId) {
        await streamingService.stopStream();
        streamingService.disconnect();
      }
      
      // Luego desconectar en el backend
      await disconnectCamera(cameraId);
    } catch (error) {
      console.error('Error al desconectar cámara:', error);
    }
  };

  const handleCameraSettings = (cameraId: string) => {
    console.log(`Abrir configuración de cámara: ${cameraId}`);
    // TODO: Implementar modal de configuración
  };

  const handleCameraCapture = async (cameraId: string) => {
    try {
      // TODO: Implementar captura con API v2
      console.log('Captura de snapshot no implementada en v2');
      addNotification({
        type: 'info',
        title: 'Función en desarrollo',
        message: 'La captura de imágenes se implementará próximamente',
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Error de captura',
        message: 'Error al capturar imagen',
      });
    }
  };

  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      {/* Toolbar superior */}
      <CameraToolbar
        connectedCameras={connectedCameras}
        totalCameras={cameras.size}
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
          cameras={cameraData}
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
