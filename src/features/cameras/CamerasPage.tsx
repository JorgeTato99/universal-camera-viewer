/**
 * 🎯 Cameras Page - Universal Camera Viewer
 * Página principal de gestión de cámaras con nuevo design system
 * Optimizada con memo, callbacks memoizados y renderizado eficiente
 */

import { useState, useEffect, useCallback, useMemo, memo } from "react";
import { Box, Typography, Fade, Skeleton } from "@mui/material";
import { CameraToolbar, CameraGrid } from "./components";
import { useCameraStoreV2 } from "../../stores/cameraStore.v2";
import { streamingService } from "../../services/python/streamingService";
import { useNotificationStore } from "../../stores/notificationStore";
import { ConnectionErrorState } from "../../components/feedback/ConnectionErrorState";
import { useConnectionError } from "../../hooks/useConnectionError";

// Ya no necesitamos convertir, usamos directamente CameraResponse

const CamerasPage = memo(() => {
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
    connectAllCameras,
    disconnectAllCameras,
  } = useCameraStoreV2();
  const { addNotification } = useNotificationStore();
  const [isChangingLayout, setIsChangingLayout] = useState(false);

  // Hook para manejar errores de conexión
  const connectionErrorHandler = useConnectionError(
    async () => {
      await loadCameras();
    },
    {
      maxRetries: 3,
      baseRetryDelay: 2000,
      enableAutoRetry: true,
    }
  );

  // Cargar cámaras desde el backend
  useEffect(() => {
    loadCameras();
  }, [loadCameras]);

  // Obtener cámaras filtradas del store
  const filteredCameras = getFilteredCameras();
  
  // Transformar datos de cámaras con memoización
  const cameraData = useMemo(() => 
    filteredCameras.map((camera) => ({
      id: camera.camera_id,
      name: camera.display_name || `Cámara ${camera.camera_id}`,
      status: camera.is_connected ? 'connected' as const : 'disconnected' as const,
      ip: camera.ip_address,
      fps: camera.is_connected ? 30 : 0,
      latency: camera.is_connected ? 45 : 0,
      connectedTime: camera.is_connected ? "02:30:15" : "00:00:00",
      aspectRatio: "16:9" as const,
    })), [filteredCameras]);

  // Obtener estadísticas de cámaras
  const cameraStats = getCameraStats();
  const connectedCameras = cameraStats.connected;

  // Handlers optimizados con useCallback
  const handleGridColumnsChange = useCallback((columns: 2 | 3 | 4 | 5) => {
    setIsChangingLayout(true);
    setGridColumns(columns);

    // Resetear el estado después de la animación
    setTimeout(() => {
      setIsChangingLayout(false);
    }, 400); // Coincide con la duración de la transición del grid
  }, [setGridColumns]);

  const handleConnectAll = useCallback(async () => {
    await connectAllCameras();
  }, [connectAllCameras]);

  const handleDisconnectAll = useCallback(async () => {
    await disconnectAllCameras();
  }, [disconnectAllCameras]);

  // Handlers optimizados con useCallback para evitar re-renders
  const handleCameraConnect = useCallback(async (cameraId: string) => {
    await connectCamera(cameraId);
  }, [connectCamera]);

  const handleCameraDisconnect = useCallback(async (cameraId: string) => {
    try {
      // Primero detener el streaming WebSocket si está activo
      try {
        await streamingService.stopStream(cameraId);
        streamingService.disconnect(cameraId);
      } catch (error) {
        // Si falla al detener el stream, continuamos con la desconexión
        console.warn('Error al detener streaming:', error);
      }
      
      // Luego desconectar en el backend
      await disconnectCamera(cameraId);
    } catch (error) {
      console.error('Error al desconectar cámara:', error);
    }
  }, [disconnectCamera]);

  const handleCameraSettings = useCallback((cameraId: string) => {
    console.log(`Abrir configuración de cámara: ${cameraId}`);
    // TODO: Implementar modal de configuración
  }, []);

  const handleCameraCapture = useCallback(async (_cameraId: string) => {
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
  }, [addNotification]);

  // Mostrar error de conexión si existe
  if (connectionError && !connectionErrorHandler.isRetrying) {
    return (
      <Box sx={{ height: "100%", display: "flex", flexDirection: "column", p: 2 }}>
        <ConnectionErrorState
          errorType={connectionError.errorType}
          customMessage={connectionError.errorMessage}
          onRetry={connectionErrorHandler.retry}
          isRetrying={connectionErrorHandler.isRetrying}
          errorDetails={connectionError.errorDetails}
        />
      </Box>
    );
  }

  return (
    <Fade in timeout={600}>
      <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
        {/* Toolbar superior con animación */}
        <Fade in timeout={400} style={{ transitionDelay: '100ms' }}>
          <Box>
            <CameraToolbar
              connectedCameras={connectedCameras}
              totalCameras={cameras.size}
              gridColumns={gridColumns as 2 | 3 | 4 | 5}
              onGridColumnsChange={handleGridColumnsChange}
              onConnectAll={handleConnectAll}
              onDisconnectAll={handleDisconnectAll}
            />
          </Box>
        </Fade>

        {/* Grid de cámaras con animación */}
        <Fade in timeout={600} style={{ transitionDelay: '200ms' }}>
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
              gridColumns={gridColumns as 2 | 3 | 4 | 5}
              isLoading={isLoading}
              onCameraConnect={handleCameraConnect}
              onCameraDisconnect={handleCameraDisconnect}
              onCameraSettings={handleCameraSettings}
              onCameraCapture={handleCameraCapture}
            />
          </Box>
        </Fade>
      </Box>
    </Fade>
  );
});

// Añadir displayName para debugging
CamerasPage.displayName = 'CamerasPage';

export default CamerasPage;
