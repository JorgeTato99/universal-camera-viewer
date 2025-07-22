/**
 * 🪝 usePublishing Hook - Universal Camera Viewer
 * Hook principal para gestión de publicaciones MediaMTX
 */

import { useCallback, useEffect } from 'react';
import { usePublishingStore } from '../../../stores/publishingStore';
import { PublishingStatus } from '../types';

/**
 * Hook para control de publicaciones
 */
export function usePublishing(cameraId?: string) {
  const {
    activePublications,
    isPublishing,
    error,
    startPublishing,
    stopPublishing,
    fetchPublishingStatus,
    clearError,
    getPublicationByCameraId,
    isPublishingActive
  } = usePublishingStore();

  // Obtener publicación específica si se proporciona cameraId
  const publication = cameraId ? getPublicationByCameraId(cameraId) : undefined;
  const isActive = cameraId ? isPublishingActive(cameraId) : false;
  const isTransitioning = cameraId ? isPublishing.get(cameraId) || false : false;

  // Función para toggle de publicación
  const togglePublishing = useCallback(async (targetCameraId?: string) => {
    const id = targetCameraId || cameraId;
    if (!id) return;

    const currentPublication = getPublicationByCameraId(id);
    
    if (currentPublication && 
        (currentPublication.status === PublishingStatus.PUBLISHING || 
         currentPublication.status === PublishingStatus.STARTING ||
         currentPublication.status === PublishingStatus.RECONNECTING)) {
      await stopPublishing(id);
    } else {
      await startPublishing(id);
    }
  }, [cameraId, startPublishing, stopPublishing, getPublicationByCameraId]);

  // Función para actualizar estado
  const refresh = useCallback(async () => {
    await fetchPublishingStatus();
  }, [fetchPublishingStatus]);

  // Limpiar error al desmontar
  useEffect(() => {
    return () => {
      if (error) clearError();
    };
  }, [error, clearError]);

  return {
    // Estado
    publication,
    activePublications,
    isActive,
    isTransitioning,
    error,
    
    // Acciones
    startPublishing,
    stopPublishing,
    togglePublishing,
    refresh,
    clearError
  };
}