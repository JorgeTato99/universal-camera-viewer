/**
 * 🎯 Cameras Page - Universal Camera Viewer
 * Página principal de gestión de cámaras con nuevo design system
 */

import React, { useState, useEffect } from "react";
import { Box, Typography } from "@mui/material";
import { CameraToolbar, CameraGrid } from "./components";
import { useCameraStore } from "../../stores";
import { cameraService } from "../../services/python/cameraService";
import { useNotificationStore } from "../../stores/notificationStore";
import { Camera, ConnectionStatus, ProtocolType } from "../../types/camera.types";
import { CameraInfo } from "../../types/service.types";

// Función para convertir CameraInfo (de la API) a Camera (del store)
const convertApiCameraToStoreCamera = (apiCamera: CameraInfo): Camera => {
  return {
    camera_id: apiCamera.camera_id,
    brand: apiCamera.brand,
    model: apiCamera.model || 'Unknown',
    display_name: apiCamera.display_name,
    connection_config: {
      ip: apiCamera.ip,
      username: 'admin',
      password: apiCamera.camera_id === 'cam_192.168.1.172' 
        ? '3gfwb3ToWfeWNqm22223DGbzcH-4si' 
        : 'admin',
      rtsp_port: 554,
      onvif_port: 80,
      http_port: 80,
      timeout: 10,
      max_retries: 3,
      retry_delay: 1000,
    },
    stream_config: {
      channel: 1,
      subtype: 0,
      resolution: '1920x1080',
      codec: 'h264',
      fps: 30,
      bitrate: 4096,
      quality: 'high',
    },
    capabilities: {
      supported_protocols: [ProtocolType.ONVIF, ProtocolType.RTSP],
      max_resolution: '1920x1080',
      supported_codecs: ['h264', 'h265'],
      has_ptz: false,
      has_audio: true,
      has_ir: true,
      onvif_version: '2.0',
    },
    status: apiCamera.is_connected 
      ? ConnectionStatus.CONNECTED 
      : ConnectionStatus.DISCONNECTED,
    is_connected: apiCamera.is_connected,
    is_streaming: apiCamera.is_streaming,
    current_protocol: ProtocolType.ONVIF,
    stats: {
      connection_attempts: 0,
      successful_connections: 0,
      failed_connections: 0,
      total_uptime: 0,
      average_response_time: 0,
    },
    created_at: new Date().toISOString(),
    last_updated: apiCamera.last_updated,
    metadata: {},
  };
};

const CamerasPage: React.FC = () => {
  const { 
    cameras, 
    isLoading, 
    addCamera, 
    updateCamera,
    getFilteredCameras,
    getCameraCount,
    clearAllCameras
  } = useCameraStore();
  const { addNotification } = useNotificationStore();
  const [gridColumns, setGridColumns] = useState<2 | 3>(3);
  const [isChangingLayout, setIsChangingLayout] = useState(false);
  const [loadingCameras, setLoadingCameras] = useState(true);

  // Cargar cámaras desde el backend
  useEffect(() => {
    const loadCameras = async () => {
      try {
        setLoadingCameras(true);
        const cameraList = await cameraService.listCameras();
        
        // Limpiar cámaras existentes y agregar las nuevas
        clearAllCameras();
        cameraList.forEach(apiCamera => {
          const storeCamera = convertApiCameraToStoreCamera(apiCamera);
          addCamera(storeCamera);
        });
      } catch (error) {
        console.error('Error cargando cámaras:', error);
        addNotification({
          type: 'error',
          title: 'Error',
          message: 'Error al cargar las cámaras',
        });
      } finally {
        setLoadingCameras(false);
      }
    };

    loadCameras();
  }, [addCamera, addNotification]);

  // Obtener cámaras filtradas del store
  const filteredCameras = getFilteredCameras();
  
  // Transformar datos de cámaras para el componente
  const cameraData = filteredCameras.map((camera: Camera) => ({
    id: camera.camera_id,
    name: camera.display_name || `Cámara ${camera.camera_id}`,
    status: camera.is_connected ? 'connected' as const : 'disconnected' as const,
    ip: camera.connection_config.ip,
    fps: camera.is_connected ? 30 : 0, // Mock FPS por ahora
    latency: camera.is_connected ? 45 : 0, // Mock latency por ahora
    connectedTime: camera.is_connected ? "02:30:15" : "00:00:00", // Mock por ahora
    aspectRatio: "16:9" as const,
  }));

  // Obtener conteo de cámaras
  const cameraCount = getCameraCount();
  const connectedCameras = cameraCount.connected;

  const handleGridColumnsChange = (columns: 2 | 3) => {
    setIsChangingLayout(true);
    setGridColumns(columns);

    // Resetear el estado después de la animación
    setTimeout(() => {
      setIsChangingLayout(false);
    }, 400); // Coincide con la duración de la transición del grid
  };

  const handleConnectAll = async () => {
    const allCameras: Camera[] = Array.from(cameras.values());
    const disconnectedCameras = allCameras.filter((cam: Camera) => !cam.is_connected);
    
    for (const camera of disconnectedCameras as Camera[]) {
      try {
        await cameraService.connectCamera(camera.camera_id, {
          ip: camera.connection_config.ip,
          username: 'admin',
          password: camera.camera_id === 'cam_192.168.1.172' 
            ? '3gfwb3ToWfeWNqm22223DGbzcH-4si' 
            : 'admin',
          protocol: 'ONVIF',
          port: 80
        });
      } catch (error) {
        console.error(`Error conectando ${camera.camera_id}:`, error);
      }
    }
    
    // Recargar cámaras
    const updatedCameras = await cameraService.listCameras();
    cameras.clear();
    updatedCameras.forEach((apiCamera: CameraInfo) => {
      const storeCamera = convertApiCameraToStoreCamera(apiCamera);
      addCamera(storeCamera);
    });
  };

  const handleDisconnectAll = async () => {
    const allCameras: Camera[] = Array.from(cameras.values());
    const connectedCameras = allCameras.filter((cam: Camera) => cam.is_connected);
    
    for (const camera of connectedCameras as Camera[]) {
      try {
        await cameraService.disconnectCamera(camera.camera_id);
      } catch (error) {
        console.error(`Error desconectando ${camera.camera_id}:`, error);
      }
    }
    
    // Recargar cámaras
    const updatedCameras = await cameraService.listCameras();
    cameras.clear();
    updatedCameras.forEach((apiCamera: CameraInfo) => {
      const storeCamera = convertApiCameraToStoreCamera(apiCamera);
      addCamera(storeCamera);
    });
  };

  // Handlers para acciones de cámaras individuales
  const handleCameraConnect = async (cameraId: string) => {
    try {
      const camera = cameras.get(cameraId);
      if (!camera) return;

      await cameraService.connectCamera(cameraId, {
        ip: camera.connection_config.ip,
        username: 'admin',
        password: cameraId === 'cam_192.168.1.172' 
          ? '3gfwb3ToWfeWNqm22223DGbzcH-4si' 
          : 'admin',
        protocol: 'ONVIF',
        port: 80
      });

      // Recargar cámaras
      const updatedCameras = await cameraService.listCameras();
      cameras.clear();
      updatedCameras.forEach((apiCamera: CameraInfo) => {
        const storeCamera = convertApiCameraToStoreCamera(apiCamera);
        addCamera(storeCamera);
      });
      
      addNotification({
        type: 'success',
        title: 'Conexión exitosa',
        message: `Cámara ${camera.display_name} conectada`,
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Error de conexión',
        message: `Error al conectar la cámara`,
      });
    }
  };

  const handleCameraDisconnect = async (cameraId: string) => {
    try {
      await cameraService.disconnectCamera(cameraId);
      
      const camera = cameras.get(cameraId);
      
      // Recargar cámaras
      const updatedCameras = await cameraService.listCameras();
      cameras.clear();
      updatedCameras.forEach((apiCamera: CameraInfo) => {
        const storeCamera = convertApiCameraToStoreCamera(apiCamera);
        addCamera(storeCamera);
      });
      
      addNotification({
        type: 'success',
        title: 'Desconexión exitosa',
        message: `Cámara ${camera?.display_name} desconectada`,
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Error de desconexión',
        message: `Error al desconectar la cámara`,
      });
    }
  };

  const handleCameraSettings = (cameraId: string) => {
    console.log(`Abrir configuración de cámara: ${cameraId}`);
    // TODO: Implementar modal de configuración
  };

  const handleCameraCapture = async (cameraId: string) => {
    try {
      const snapshot = await cameraService.captureSnapshot(cameraId);
      
      // Descargar imagen
      const link = document.createElement('a');
      link.href = `data:image/jpeg;base64,${snapshot.image_data}`;
      link.download = `snapshot_${cameraId}_${new Date().getTime()}.jpg`;
      link.click();
      
      addNotification({
        type: 'success',
        title: 'Captura exitosa',
        message: 'Captura guardada',
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
          isLoading={loadingCameras || isLoading}
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
