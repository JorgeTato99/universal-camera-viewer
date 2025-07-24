/**
 * 🪝 Remote Publishing Hook - Universal Camera Viewer
 * Hook personalizado para gestión de publicación remota
 * 
 * Proporciona:
 * - Estado de publicación remota por cámara
 * - Acciones de control (start/stop/restart)
 * - Estado de carga y errores
 * - Métricas en tiempo real
 */

import { useState, useCallback, useEffect } from 'react';
import { usePublishingStore } from '../../../stores/publishingStore';
import { 
  mediamtxRemoteService,
  RemotePublishStatus 
} from '../../../services/publishing/mediamtxRemoteService';
import { PublishingStatus } from '../types';

interface UseRemotePublishingOptions {
  cameraId: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface UseRemotePublishingReturn {
  // Estado
  remotePublication: RemotePublishStatus | undefined;
  isPublishing: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Acciones
  startPublishing: (serverId: number, customName?: string) => Promise<boolean>;
  stopPublishing: () => Promise<boolean>;
  restartPublishing: () => Promise<boolean>;
  refreshStatus: () => Promise<void>;
  
  // Utilidades
  canPublish: boolean;
  canStop: boolean;
  statusLabel: string;
}

/**
 * Hook para gestión de publicación remota de una cámara
 */
export function useRemotePublishing({
  cameraId,
  autoRefresh = true,
  refreshInterval = 5000
}: UseRemotePublishingOptions): UseRemotePublishingReturn {
  // Estado local
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Estado global (si se integra con el store extendido)
  // Por ahora, usamos el servicio directamente
  const [remotePublication, setRemotePublication] = useState<RemotePublishStatus | undefined>();
  
  // Verificar si está publicando
  const isPublishing = remotePublication?.status === PublishingStatus.PUBLISHING;
  
  // Determinar si puede publicar o detener
  const canPublish = !isPublishing && !isLoading;
  const canStop = isPublishing && !isLoading;
  
  // Obtener etiqueta de estado
  const getStatusLabel = () => {
    if (!remotePublication) return 'Sin publicar';
    
    switch (remotePublication.status) {
      case PublishingStatus.IDLE:
        return 'Inactivo';
      case PublishingStatus.STARTING:
        return 'Iniciando...';
      case PublishingStatus.PUBLISHING:
        return 'Publicando';
      case PublishingStatus.STOPPING:
        return 'Deteniendo...';
      case PublishingStatus.ERROR:
        return 'Error';
      default:
        return 'Desconocido';
    }
  };
  
  // Refrescar estado
  const refreshStatus = useCallback(async () => {
    try {
      const cached = mediamtxRemoteService.getCachedRemotePublication(cameraId);
      if (cached) {
        setRemotePublication(cached);
      }
      
      // Obtener estado actualizado del servidor
      const response = await mediamtxRemoteService.getRemotePublicationStatus(cameraId);
      if (response.success && response.data) {
        setRemotePublication(response.data);
        setError(null);
      }
    } catch (err) {
      // Si es 404, no hay publicación activa
      if (err instanceof Error && err.message.includes('404')) {
        setRemotePublication(undefined);
      } else {
        console.error('Error refrescando estado:', err);
      }
    }
  }, [cameraId]);
  
  // Iniciar publicación
  const startPublishing = useCallback(async (
    serverId: number,
    customName?: string
  ): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await mediamtxRemoteService.startRemotePublishing({
        camera_id: cameraId,
        server_id: serverId,
        custom_name: customName
      });
      
      if (response.success && response.data) {
        setRemotePublication(response.data);
        return true;
      } else {
        setError(response.error || 'Error al iniciar publicación');
        return false;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [cameraId]);
  
  // Detener publicación
  const stopPublishing = useCallback(async (): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      await mediamtxRemoteService.stopRemotePublishing(cameraId);
      setRemotePublication(undefined);
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [cameraId]);
  
  // Reiniciar publicación
  const restartPublishing = useCallback(async (): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await mediamtxRemoteService.restartRemotePublishing(cameraId);
      
      if (response.success && response.data) {
        setRemotePublication(response.data);
        return true;
      } else {
        setError(response.error || 'Error al reiniciar publicación');
        return false;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [cameraId]);
  
  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;
    
    // Refresh inicial
    refreshStatus();
    
    // Configurar intervalo
    const interval = setInterval(refreshStatus, refreshInterval);
    
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, refreshStatus]);
  
  return {
    // Estado
    remotePublication,
    isPublishing,
    isLoading,
    error,
    
    // Acciones
    startPublishing,
    stopPublishing,
    restartPublishing,
    refreshStatus,
    
    // Utilidades
    canPublish,
    canStop,
    statusLabel: getStatusLabel()
  };
}