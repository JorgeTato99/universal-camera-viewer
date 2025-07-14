/**
 * Hook personalizado para gestión de cámaras
 */

import { useState, useCallback } from 'react';
import { useCameraStore } from '../stores/cameraStore';
import { cameraService } from '../services/python/cameraService';
import { ConnectionConfig } from '../types/service.types';

export const useCamera = (cameraId: string) => {
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { 
    cameras, 
    updateCameraStatus,
    updateCameraConnection 
  } = useCameraStore();
  
  const camera = cameras.find(cam => cam.camera_id === cameraId);

  const connect = useCallback(async (config?: ConnectionConfig) => {
    if (!camera) {
      setError('Cámara no encontrada');
      return false;
    }

    setIsConnecting(true);
    setError(null);

    try {
      // Actualizar estado a "conectando"
      updateCameraStatus(cameraId, 'connecting');

      // Configuración por defecto si no se proporciona
      const connectionConfig: ConnectionConfig = config || {
        ip: camera.ip,
        username: 'admin',
        password: camera.camera_id === 'cam_192.168.1.172' 
          ? '3gfwb3ToWfeWNqm22223DGbzcH-4si' // Credencial real para Dahua
          : 'admin',
        protocol: 'ONVIF',
        port: 80
      };

      // Conectar usando el servicio
      await cameraService.connectCamera(cameraId, connectionConfig);

      // Actualizar estado a "conectado"
      updateCameraConnection(cameraId, true);
      updateCameraStatus(cameraId, 'connected');
      
      setIsConnecting(false);
      return true;
    } catch (err) {
      console.error('Error conectando cámara:', err);
      setError(err instanceof Error ? err.message : 'Error de conexión');
      updateCameraStatus(cameraId, 'error');
      updateCameraConnection(cameraId, false);
      setIsConnecting(false);
      return false;
    }
  }, [camera, cameraId, updateCameraStatus, updateCameraConnection]);

  const disconnect = useCallback(async () => {
    if (!camera) {
      setError('Cámara no encontrada');
      return false;
    }

    try {
      // Desconectar usando el servicio
      await cameraService.disconnectCamera(cameraId);

      // Actualizar estado
      updateCameraConnection(cameraId, false);
      updateCameraStatus(cameraId, 'disconnected');
      
      return true;
    } catch (err) {
      console.error('Error desconectando cámara:', err);
      setError(err instanceof Error ? err.message : 'Error al desconectar');
      return false;
    }
  }, [camera, cameraId, updateCameraConnection, updateCameraStatus]);

  const captureSnapshot = useCallback(async () => {
    if (!camera || !camera.is_connected) {
      setError('La cámara debe estar conectada');
      return null;
    }

    try {
      const snapshot = await cameraService.captureSnapshot(cameraId);
      return snapshot;
    } catch (err) {
      console.error('Error capturando snapshot:', err);
      setError(err instanceof Error ? err.message : 'Error al capturar');
      return null;
    }
  }, [camera, cameraId]);

  return {
    camera,
    isConnecting,
    error,
    connect,
    disconnect,
    captureSnapshot,
  };
};