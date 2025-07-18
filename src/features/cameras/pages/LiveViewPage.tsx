/**
 * 🎥 Live View Page - Universal Camera Viewer
 * Página de visualización en vivo de cámaras activas
 * Optimizada para rendimiento con memoización y virtualización
 */

import React, { useState, useEffect, useMemo, useCallback, memo } from "react";
import { Box, Typography, Fade, Grow, CircularProgress } from "@mui/material";
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
          title: 'Error de Conexión',
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
      type: "info",
      title: "Actualización Completa",
      message: "Cámaras actualizadas",
    });
  }, [loadCameras, addNotification]);

  const handleConnect = useCallback(async (cameraId: string) => {
    try {
      await connectCamera(cameraId);
      addNotification({
        type: "success",
        title: "Conexión Exitosa",
        message: "Cámara conectada exitosamente",
      });
    } catch (error) {
      addNotification({
        type: "error",
        title: "Error de Conexión",
        message: "Error al conectar la cámara",
      });
    }
  }, [connectCamera, addNotification]);

  const handleDisconnect = useCallback(async (cameraId: string) => {
    try {
      await disconnectCamera(cameraId);
      addNotification({
        type: "info",
        title: "Desconexión",
        message: "Cámara desconectada",
      });
    } catch (error) {
      addNotification({
        type: "error",
        title: "Error de Desconexión",
        message: "Error al desconectar la cámara",
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
        type: "info",
        title: "Conexión Múltiple",
        message: "Conectando todas las cámaras...",
      });
    } catch (error) {
      addNotification({
        type: "error",
        title: "Error de Conexión Múltiple",
        message: "Error al conectar las cámaras",
      });
    }
  }, [addNotification]);

  const handleDisconnectAll = useCallback(async () => {
    try {
      // TODO: Implementar desconectar todas las cámaras
      addNotification({
        type: "info",
        title: "Desconexión Múltiple",
        message: "Desconectando todas las cámaras...",
      });
    } catch (error) {
      addNotification({
        type: "error",
        title: "Error de Desconexión Múltiple",
        message: "Error al desconectar las cámaras",
      });
    }
  }, [addNotification]);

  return (
    <Fade in timeout={600}>
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
          <Fade in timeout={400}>
            <Box>
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
            </Box>
          </Fade>
        ) : (
          <>
            {/* Header con título y estadísticas con animación */}
            <Fade in timeout={500} style={{ transitionDelay: '100ms' }}>
              <Box>
                <Typography variant="h4" component="h1" gutterBottom>
                  Vista en Vivo
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {connectedCameras.length} cámara{connectedCameras.length !== 1 ? 's' : ''} disponible{connectedCameras.length !== 1 ? 's' : ''} para visualización
                </Typography>
              </Box>
            </Fade>

            {/* Toolbar con controles específicos de vista en vivo */}
            <Fade in timeout={600} style={{ transitionDelay: '200ms' }}>
              <Box>
                <CameraToolbar
                  totalCameras={connectedCameras.length}
                  connectedCameras={stats.connected}
                  gridColumns={gridColumns as 2 | 3 | 4 | 5}
                  onGridColumnsChange={handleLayoutChange}
                  onConnectAll={handleConnectAll}
                  onDisconnectAll={handleDisconnectAll}
                />
              </Box>
            </Fade>

            {/* Grid de cámaras en vivo con animación */}
            <Grow in timeout={800} style={{ transitionDelay: '300ms', transformOrigin: '0 0 0' }}>
              <Box sx={{ flex: 1, overflow: "auto" }}>
                <CameraGrid
                  cameras={cameraData}
                  isLoading={isLoading || isChangingLayout}
                  gridColumns={gridColumns as 2 | 3 | 4 | 5}
                  onCameraConnect={handleConnect}
                  onCameraDisconnect={handleDisconnect}
                />
              </Box>
            </Grow>
          </>
        )}
      </Box>
    </Fade>
  );
});

// Añadir displayName para debugging
LiveViewPage.displayName = 'LiveViewPage';

export default LiveViewPage;