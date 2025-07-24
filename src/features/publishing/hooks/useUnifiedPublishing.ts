/**
 * 🔄 Unified Publishing Hook - Universal Camera Viewer
 * Hook personalizado para gestión unificada de publicaciones locales y remotas
 * 
 * Proporciona:
 * - Vista unificada de publicaciones (local + remota)
 * - Métricas agregadas
 * - Control inteligente de publicación
 * - Detección automática de conflictos
 */

import { useCallback, useMemo } from 'react';
import { usePublishingStore } from '../../../stores/publishingStore';
import { PublishingStatus } from '../types';

interface UseUnifiedPublishingReturn {
  // Estado unificado
  unifiedMetrics: ReturnType<typeof usePublishingStore>['unifiedMetrics'];
  
  // Publicaciones por cámara
  getUnifiedPublication: (cameraId: string) => {
    local?: ReturnType<typeof usePublishingStore>['getPublicationByCameraId'];
    remote?: ReturnType<typeof usePublishingStore>['getRemotePublicationByCameraId'];
    isPublishing: boolean;
    publishingType: 'none' | 'local' | 'remote' | 'both';
  };
  
  // Acciones inteligentes
  startPublishing: (cameraId: string, options?: {
    preferRemote?: boolean;
    serverId?: number;
    forceRestart?: boolean;
  }) => Promise<void>;
  
  stopPublishing: (cameraId: string, options?: {
    stopLocal?: boolean;
    stopRemote?: boolean;
  }) => Promise<void>;
  
  // Utilidades
  canPublish: (cameraId: string, type: 'local' | 'remote') => boolean;
  getPublishingStatus: (cameraId: string) => {
    status: PublishingStatus | 'mixed';
    label: string;
    color: string;
  };
  
  // Resumen general
  getSummary: () => {
    totalPublications: number;
    localPublications: number;
    remotePublications: number;
    totalViewers: number;
    totalBandwidthMbps: number;
    healthStatus: 'healthy' | 'warning' | 'error';
  };
}

/**
 * Hook para gestión unificada de publicaciones
 */
export function useUnifiedPublishing(): UseUnifiedPublishingReturn {
  // Estado y acciones del store
  const unifiedMetrics = usePublishingStore((state) => state.unifiedMetrics);
  const getUnifiedPublication = usePublishingStore((state) => state.getUnifiedPublication);
  const activePublications = usePublishingStore((state) => state.activePublications);
  const remotePublications = usePublishingStore((state) => state.remote.publications);
  const selectedServerId = usePublishingStore((state) => state.remote.selectedServerId);
  const authenticatedServers = usePublishingStore((state) => state.getAuthenticatedServers());
  
  // Acciones
  const startLocalPublishing = usePublishingStore((state) => state.startPublishing);
  const stopLocalPublishing = usePublishingStore((state) => state.stopPublishing);
  const startRemotePublishing = usePublishingStore((state) => state.startRemotePublishing);
  const stopRemotePublishing = usePublishingStore((state) => state.stopRemotePublishing);
  const isPublishing = usePublishingStore((state) => state.isPublishing);
  
  // Iniciar publicación inteligente
  const startPublishing = useCallback(async (
    cameraId: string,
    options?: {
      preferRemote?: boolean;
      serverId?: number;
      forceRestart?: boolean;
    }
  ) => {
    const { preferRemote = false, serverId, forceRestart = false } = options || {};
    const unified = getUnifiedPublication(cameraId);
    
    // Si ya está publicando y no es forzado, no hacer nada
    if (unified.isPublishing && !forceRestart) {
      console.log('La cámara ya está publicando');
      return;
    }
    
    // Determinar tipo de publicación
    if (preferRemote || serverId) {
      // Publicación remota
      const targetServerId = serverId || selectedServerId;
      
      if (!targetServerId) {
        throw new Error('No se ha seleccionado un servidor remoto');
      }
      
      // Si está publicando localmente, detener primero
      if (unified.local && unified.local.status === PublishingStatus.PUBLISHING) {
        await stopLocalPublishing(cameraId);
      }
      
      // Iniciar publicación remota
      await startRemotePublishing(cameraId, targetServerId);
    } else {
      // Publicación local por defecto
      
      // Si está publicando remotamente, detener primero
      if (unified.remote && unified.remote.status === PublishingStatus.PUBLISHING) {
        await stopRemotePublishing(cameraId);
      }
      
      // Iniciar publicación local
      await startLocalPublishing(cameraId, forceRestart);
    }
  }, [
    getUnifiedPublication,
    selectedServerId,
    startLocalPublishing,
    stopLocalPublishing,
    startRemotePublishing,
    stopRemotePublishing
  ]);
  
  // Detener publicación inteligente
  const stopPublishing = useCallback(async (
    cameraId: string,
    options?: {
      stopLocal?: boolean;
      stopRemote?: boolean;
    }
  ) => {
    const { stopLocal = true, stopRemote = true } = options || {};
    const unified = getUnifiedPublication(cameraId);
    
    const promises: Promise<void>[] = [];
    
    // Detener publicación local si está activa
    if (stopLocal && unified.local && unified.local.status === PublishingStatus.PUBLISHING) {
      promises.push(stopLocalPublishing(cameraId));
    }
    
    // Detener publicación remota si está activa
    if (stopRemote && unified.remote && unified.remote.status === PublishingStatus.PUBLISHING) {
      promises.push(stopRemotePublishing(cameraId));
    }
    
    // Esperar a que ambas se detengan
    await Promise.all(promises);
  }, [getUnifiedPublication, stopLocalPublishing, stopRemotePublishing]);
  
  // Verificar si puede publicar
  const canPublish = useCallback((cameraId: string, type: 'local' | 'remote'): boolean => {
    // No puede si está procesando
    if (isPublishing.get(cameraId)) {
      return false;
    }
    
    const unified = getUnifiedPublication(cameraId);
    
    if (type === 'local') {
      // No puede publicar localmente si ya está publicando localmente
      return !unified.local || unified.local.status !== PublishingStatus.PUBLISHING;
    } else {
      // No puede publicar remotamente si:
      // 1. Ya está publicando remotamente
      if (unified.remote && unified.remote.status === PublishingStatus.PUBLISHING) {
        return false;
      }
      
      // 2. No hay servidores autenticados
      if (authenticatedServers.length === 0) {
        return false;
      }
      
      return true;
    }
  }, [isPublishing, getUnifiedPublication, authenticatedServers]);
  
  // Obtener estado de publicación
  const getPublishingStatus = useCallback((cameraId: string) => {
    const unified = getUnifiedPublication(cameraId);
    
    // Determinar estado principal
    let status: PublishingStatus | 'mixed' = PublishingStatus.IDLE;
    let label = 'Inactivo';
    let color = '#9e9e9e';
    
    // Si ambos están publicando
    if (unified.publishingType === 'both') {
      status = 'mixed';
      label = 'Publicando (Local + Remoto)';
      color = '#2196f3';
    } else if (unified.local && unified.local.status !== PublishingStatus.IDLE) {
      // Estado local tiene prioridad
      status = unified.local.status;
      label = `${getStatusLabel(status)} (Local)`;
      color = getStatusColor(status);
    } else if (unified.remote && unified.remote.status !== PublishingStatus.IDLE) {
      // Estado remoto
      status = unified.remote.status;
      label = `${getStatusLabel(status)} (Remoto)`;
      color = getStatusColor(status);
    }
    
    return { status, label, color };
  }, [getUnifiedPublication]);
  
  // Obtener resumen general
  const getSummary = useCallback(() => {
    const localPubs = Array.from(activePublications.values());
    const remotePubs = Array.from(remotePublications.values());
    
    // Contar publicaciones activas
    const activeLocalCount = localPubs.filter(p => 
      p.status === PublishingStatus.PUBLISHING
    ).length;
    
    const activeRemoteCount = remotePubs.filter(p => 
      p.status === PublishingStatus.PUBLISHING
    ).length;
    
    // Determinar estado de salud
    let healthStatus: 'healthy' | 'warning' | 'error' = 'healthy';
    
    const errorCount = localPubs.filter(p => p.status === PublishingStatus.ERROR).length +
                      remotePubs.filter(p => p.status === PublishingStatus.ERROR).length;
    
    if (errorCount > 0) {
      healthStatus = 'error';
    } else if (activeLocalCount + activeRemoteCount === 0) {
      healthStatus = 'warning';
    }
    
    return {
      totalPublications: unifiedMetrics.totalPublications,
      localPublications: unifiedMetrics.localPublications,
      remotePublications: unifiedMetrics.remotePublications,
      totalViewers: unifiedMetrics.totalViewers,
      totalBandwidthMbps: unifiedMetrics.totalBandwidthMbps,
      healthStatus
    };
  }, [activePublications, remotePublications, unifiedMetrics]);
  
  return {
    // Estado unificado
    unifiedMetrics,
    
    // Publicaciones por cámara
    getUnifiedPublication,
    
    // Acciones inteligentes
    startPublishing,
    stopPublishing,
    
    // Utilidades
    canPublish,
    getPublishingStatus,
    
    // Resumen general
    getSummary
  };
}

// Helpers internos
function getStatusLabel(status: PublishingStatus): string {
  switch (status) {
    case PublishingStatus.IDLE:
      return 'Inactivo';
    case PublishingStatus.STARTING:
      return 'Iniciando';
    case PublishingStatus.PUBLISHING:
      return 'Publicando';
    case PublishingStatus.STOPPING:
      return 'Deteniendo';
    case PublishingStatus.STOPPED:
      return 'Detenido';
    case PublishingStatus.ERROR:
      return 'Error';
    case PublishingStatus.RECONNECTING:
      return 'Reconectando';
    default:
      return 'Desconocido';
  }
}

function getStatusColor(status: PublishingStatus): string {
  switch (status) {
    case PublishingStatus.IDLE:
      return '#9e9e9e';
    case PublishingStatus.STARTING:
      return '#ff9800';
    case PublishingStatus.PUBLISHING:
      return '#4caf50';
    case PublishingStatus.STOPPING:
      return '#ff9800';
    case PublishingStatus.STOPPED:
      return '#757575';
    case PublishingStatus.ERROR:
      return '#f44336';
    case PublishingStatus.RECONNECTING:
      return '#2196f3';
    default:
      return '#9e9e9e';
  }
}