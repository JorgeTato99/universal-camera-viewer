/**
 * 🎥 Live View Page - Universal Camera Viewer
 * Página de visualización en vivo de cámaras activas
 * Optimizada para rendimiento con memoización y virtualización
 */

import React, { useState, useEffect, useMemo, useCallback, memo } from "react";
import { Box, Typography } from "@mui/material";
import { CameraToolbar, CameraGrid } from "../components";
import { useCameraStoreV2 } from "../../../stores/cameraStore.v2";
import { useNotificationStore } from "../../../stores/notificationStore";
import { ConnectionErrorState } from "../../../components/feedback/ConnectionErrorState";
import { useConnectionError } from "../../../hooks/useConnectionError";

const LiveViewPage = memo(() => {
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
    connectionError,
    clearConnectionError,
  } = useCameraStoreV2();
  const { addNotification } = useNotificationStore();
  const [isChangingLayout, setIsChangingLayout] = useState(false);

  // Hook para manejar errores de conexión con reintentos
  const connectionErrorHandler = useConnectionError(
    async () => {
      await loadCameras();
    },
    {
      maxRetries: 3,
      baseRetryDelay: 2000,
      enableAutoRetry: true,
      onMaxRetriesReached: () => {
        addNotification({
          type: 'error',
          message: 'No se pudo conectar con el servidor después de varios intentos',
          duration: 0,
        });
      },
    }
  );

  // Cargar cámaras desde el backend
  useEffect(() => {
    loadCameras();
  }, [loadCameras]);

  // Obtener cámaras filtradas - NO memorizar porque depende del estado interno del store
  const filteredCameras = getFilteredCameras();
  
  // TODO: Por ahora mostramos todas las cámaras hasta que se implemente la lógica de conexión real
  // En el futuro, filtrar solo las conectadas: filteredCameras.filter(camera => camera.is_connected)
  const connectedCameras = filteredCameras;
  
  const stats = getCameraStats();
  
  // Log para debugging solo cuando cambian las cámaras
  useEffect(() => {
    console.log('LiveViewPage - Cámaras filtradas:', filteredCameras.length);
    console.log('LiveViewPage - Cámaras "conectadas":', connectedCameras.length);
  }, [filteredCameras.length, connectedCameras.length]);
  
  // Transformar datos de cámaras para el componente con memorización
  const cameraData = useMemo(() => 
    connectedCameras.map((camera) => ({
      id: camera.camera_id,
      name: camera.display_name || `Cámara ${camera.camera_id}`,
      status: camera.is_connected ? 'connected' as const : 'disconnected' as const,
      ip: camera.ip_address,
      fps: camera.is_connected ? 30 : 0, // Mock FPS por ahora
      latency: camera.is_connected ? 45 : 0, // Mock latency por ahora
      connectedTime: camera.is_connected ? "02:30:15" : "00:00:00", // Mock por ahora
    })), [connectedCameras]);

  const handleRefresh = useCallback(async () => {
    await loadCameras();
    addNotification({
      message: "Cámaras actualizadas",
      type: "info",
    });
  }, [loadCameras, addNotification]);

  const handleConnect = useCallback(async (cameraId: string) => {
    try {
      await connectCamera(cameraId);
      addNotification({
        message: "Cámara conectada exitosamente",
        type: "success",
      });
    } catch (error) {
      addNotification({
        message: "Error al conectar la cámara",
        type: "error",
      });
    }
  }, [connectCamera, addNotification]);

  const handleDisconnect = useCallback(async (cameraId: string) => {
    try {
      await disconnectCamera(cameraId);
      addNotification({
        message: "Cámara desconectada",
        type: "info",
      });
    } catch (error) {
      addNotification({
        message: "Error al desconectar la cámara",
        type: "error",
      });
    }
  }, [disconnectCamera, addNotification]);

  const handleLayoutChange = useCallback((newColumns: 2 | 3 | 4 | 5) => {
    setIsChangingLayout(true);
    setGridColumns(newColumns);
    setTimeout(() => setIsChangingLayout(false), 300);
  }, [setGridColumns]);

  const handleConnectAll = useCallback(async () => {
    try {
      // TODO: Implementar conectar todas las cámaras
      addNotification({
        message: "Conectando todas las cámaras...",
        type: "info",
      });
    } catch (error) {
      addNotification({
        message: "Error al conectar las cámaras",
        type: "error",
      });
    }
  }, [addNotification]);

  const handleDisconnectAll = useCallback(async () => {
    try {
      // TODO: Implementar desconectar todas las cámaras
      addNotification({
        message: "Desconectando todas las cámaras...",
        type: "info",
      });
    } catch (error) {
      addNotification({
        message: "Error al desconectar las cámaras",
        type: "error",
      });
    }
  }, [addNotification]);

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        width: "100%",
        overflow: "hidden",
        gap: 2,
        p: 2,
      }}
    >
      {/* Mostrar error de conexión si existe */}
      {connectionError?.hasError ? (
        <ConnectionErrorState
          errorType={connectionError.errorType}
          customMessage={connectionError.errorMessage}
          errorDetails={connectionError.errorDetails}
          onRetry={() => {
            clearConnectionError();
            connectionErrorHandler.retry();
          }}
          isRetrying={connectionErrorHandler.isRetrying}
          showDebugInfo={true}
        />
      ) : (
        <>
          {/* Header con título y estadísticas */}
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              Vista en Vivo
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {connectedCameras.length} cámara{connectedCameras.length !== 1 ? 's' : ''} disponible{connectedCameras.length !== 1 ? 's' : ''} para visualización
            </Typography>
          </Box>

          {/* Toolbar con controles específicos de vista en vivo */}
          <CameraToolbar
            totalCameras={connectedCameras.length}
            connectedCameras={stats.connected}
            gridColumns={gridColumns as 2 | 3 | 4 | 5}
            onGridColumnsChange={handleLayoutChange}
            onConnectAll={handleConnectAll}
            onDisconnectAll={handleDisconnectAll}
          />

          {/* Grid de cámaras en vivo */}
          <Box sx={{ flex: 1, overflow: "auto" }}>
            <CameraGrid
              cameras={cameraData}
              isLoading={isLoading || isChangingLayout}
              gridColumns={gridColumns}
              onCameraConnect={handleConnect}
              onCameraDisconnect={handleDisconnect}
            />
          </Box>
        </>
      )}
    </Box>
  );
});

// Añadir displayName para debugging
LiveViewPage.displayName = 'LiveViewPage';

export default LiveViewPage;