/**
 * 🪝 Remote Publishing Hook - Universal Camera Viewer
 * Hook personalizado para gestión de publicación remota
 * 
 * Proporciona:
 * - Estado de publicación remota por cámara
 * - Acciones de control (start/stop/restart)
 * - Estado de carga y errores
 * - Métricas en tiempo real
 * - Integración completa con el store unificado
 */

import { useCallback, useEffect } from 'react';
import { usePublishingStore } from '../../../stores/publishingStore';
import { PublishingStatus } from '../types';

interface UseRemotePublishingOptions {
  cameraId: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface UseRemotePublishingReturn {
  // Estado
  remotePublication: ReturnType<typeof usePublishingStore.getState>['getRemotePublicationByCameraId'] extends (cameraId: string) => infer R ? R : undefined;
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
 * Usa el store unificado para estado centralizado
 */
export function useRemotePublishing({
  cameraId,
  autoRefresh = true,
  refreshInterval = 30000 // Incrementado de 5s a 30s para reducir carga del servidor
}: UseRemotePublishingOptions): UseRemotePublishingReturn {
  // Estado desde el store unificado
  const remotePublication = usePublishingStore((state) => state.getRemotePublicationByCameraId(cameraId));
  const isLoadingMap = usePublishingStore((state) => state.isPublishing);
  const error = usePublishingStore((state) => state.error);
  
  // Acciones del store
  const startRemotePublishing = usePublishingStore((state) => state.startRemotePublishing);
  const stopRemotePublishing = usePublishingStore((state) => state.stopRemotePublishing);
  const fetchRemotePublications = usePublishingStore((state) => state.fetchRemotePublications);
  const clearError = usePublishingStore((state) => state.clearError);
  
  // Estado derivado
  const isLoading = isLoadingMap.get(cameraId) || false;
  
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
  
  // Refrescar estado (usa store)
  const refreshStatus = useCallback(async () => {
    try {
      await fetchRemotePublications();
    } catch (err) {
      console.error('Error refrescando publicaciones remotas:', err);
    }
  }, [fetchRemotePublications]);
  
  // Iniciar publicación (usa store)
  const startPublishing = useCallback(async (
    serverId: number,
    _customName?: string // Prefijo con _ para indicar que no se usa
  ): Promise<boolean> => {
    clearError();
    
    try {
      // TODO: Implementar soporte para customName en el store
      await startRemotePublishing(cameraId, serverId);
      return true;
    } catch (err) {
      return false;
    }
  }, [cameraId, startRemotePublishing, clearError]);
  
  // Detener publicación (usa store)
  const stopPublishing = useCallback(async (): Promise<boolean> => {
    clearError();
    
    try {
      await stopRemotePublishing(cameraId);
      return true;
    } catch (err) {
      return false;
    }
  }, [cameraId, stopRemotePublishing, clearError]);
  
  // Reiniciar publicación
  const restartPublishing = useCallback(async (): Promise<boolean> => {
    if (!remotePublication) {
      return false;
    }
    
    clearError();
    
    try {
      // Detener primero
      await stopRemotePublishing(cameraId);
      
      // Esperar un momento
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Volver a iniciar con el mismo servidor
      await startRemotePublishing(cameraId, remotePublication.server_id);
      return true;
    } catch (err) {
      return false;
    }
  }, [cameraId, remotePublication, startRemotePublishing, stopRemotePublishing, clearError]);
  
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