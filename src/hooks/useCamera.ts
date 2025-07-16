/**
 * Hook personalizado para gestión de cámaras
 * Actualizado para la estructura v2 con base de datos 3FN
 */

import { useState, useCallback } from 'react';
import { useCameraStoreV2 } from '../stores/cameraStore.v2';
import { cameraServiceV2 } from '../services/python/cameraService.v2';
import { ConnectionStatus } from '../types/camera.types.v2';

export const useCamera = (cameraId: string) => {
  const [error, setError] = useState<string | null>(null);
  
  const { 
    cameras, 
    connectCamera,
    disconnectCamera,
    updateCamera,
    isConnecting,
    errors
  } = useCameraStoreV2();
  
  const camera = cameras.get(cameraId);
  const isConnectingCamera = isConnecting.get(cameraId) || false;
  const cameraError = errors.get(cameraId);

  const connect = useCallback(async () => {
    if (!camera) {
      setError('Cámara no encontrada');
      return false;
    }

    setError(null);

    try {
      // Conectar usando el store v2 que maneja todo internamente
      await connectCamera(cameraId);
      return true;
    } catch (err) {
      console.error('Error conectando cámara:', err);
      setError(err instanceof Error ? err.message : 'Error de conexión');
      return false;
    }
  }, [camera, cameraId, connectCamera]);

  const disconnect = useCallback(async () => {
    if (!camera) {
      setError('Cámara no encontrada');
      return false;
    }

    try {
      // Desconectar usando el store v2
      await disconnectCamera(cameraId);
      return true;
    } catch (err) {
      console.error('Error desconectando cámara:', err);
      setError(err instanceof Error ? err.message : 'Error al desconectar');
      return false;
    }
  }, [camera, cameraId, disconnectCamera]);

  const captureSnapshot = useCallback(async () => {
    if (!camera || !camera.is_connected) {
      setError('La cámara debe estar conectada');
      return null;
    }

    try {
      // TODO: Implementar captura de snapshot en v2
      console.log('Captura de snapshot pendiente de implementación en v2');
      setError('Función en desarrollo');
      return null;
    } catch (err) {
      console.error('Error capturando snapshot:', err);
      setError(err instanceof Error ? err.message : 'Error al capturar');
      return null;
    }
  }, [camera, cameraId]);

  return {
    camera,
    isConnecting: isConnectingCamera,
    error: error || cameraError,
    connect,
    disconnect,
    captureSnapshot,
  };
};