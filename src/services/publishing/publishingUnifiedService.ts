/**
 * Servicio unificado para gestión de publicaciones locales y remotas
 * Proporciona una vista agregada de todas las publicaciones activas
 * 
 * @module services/publishing/publishingUnifiedService
 * 
 * @todo Funcionalidades pendientes:
 * - Implementar caché inteligente para reducir llamadas a la API
 * - Agregar soporte para publicación en múltiples servidores simultáneos
 * - Implementar cola de reintentos para publicaciones fallidas
 * - Agregar métricas de rendimiento del servicio
 * - Implementar throttling para evitar sobrecarga de API
 * 
 * @note Este servicio es el punto único de entrada para toda la gestión de publicaciones
 */

import { apiClient } from '../api/apiClient';
import { notificationStore } from '../../stores/notificationStore';
import type { ApiResponse } from '../../types/api.types';

// ====================================================================
// Types & Interfaces
// ====================================================================

/**
 * Tipos de publicación soportados
 */
export type PublicationType = 'local' | 'remote';

/**
 * Estado de una publicación
 */
export type PublicationStatus = 'publishing' | 'error' | 'stopped' | 'starting' | 'stopping';

/**
 * Publicación unificada (local o remota)
 */
export interface UnifiedPublication {
  // Identificadores
  camera_id: string;
  publication_type: PublicationType;
  server_id?: number; // Solo para publicaciones remotas
  server_name?: string; // Nombre del servidor (local o remoto)
  
  // Estado
  status: PublicationStatus;
  started_at: string | null;
  error_message?: string;
  
  // Métricas
  metrics: {
    fps: number;
    bitrate_kbps: number;
    viewers: number;
    uptime_seconds: number;
    latency_ms?: number;
  };
  
  // URLs
  stream_url?: string;
  webrtc_url?: string; // Solo para remotas
  
  // Metadatos
  camera_name: string;
  camera_ip: string;
  resolution?: string;
}

/**
 * Resumen de publicaciones
 */
export interface PublishingSummary {
  total_publications: number;
  local_publications: number;
  remote_publications: number;
  total_viewers: number;
  total_servers: number;
  active_servers: number;
  total_bitrate_mbps: number;
  average_fps: number;
  servers_breakdown: Array<{
    server_id: number | null;
    server_name: string;
    publication_count: number;
    viewer_count: number;
  }>;
}

/**
 * Filtros para publicaciones
 */
export interface PublicationFilters {
  type?: PublicationType;
  server_id?: number;
  status?: PublicationStatus;
  search?: string;
}

/**
 * Comando para publicación remota
 */
export interface RemotePublishCommand {
  server_id: number;
  stream_key?: string; // Opcional, se genera automáticamente si no se proporciona
  metadata?: Record<string, any>;
}

// ====================================================================
// Service Implementation
// ====================================================================

/**
 * Servicio unificado de publicaciones
 * Combina publicaciones locales (MediaMTX local) y remotas
 */
class PublishingUnifiedService {
  private static instance: PublishingUnifiedService;
  
  private constructor() {}

  /**
   * Obtiene la instancia única del servicio
   */
  static getInstance(): PublishingUnifiedService {
    if (!PublishingUnifiedService.instance) {
      PublishingUnifiedService.instance = new PublishingUnifiedService();
    }
    return PublishingUnifiedService.instance;
  }

  /**
   * Obtiene todas las publicaciones activas (local + remoto)
   */
  async getAllPublications(filters?: PublicationFilters): Promise<UnifiedPublication[]> {
    try {
      // Construir parámetros de consulta
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.server_id) params.append('server_id', filters.server_id.toString());
      if (filters?.status) params.append('status', filters.status);
      if (filters?.search) params.append('search', filters.search);

      const response = await apiClient.get<ApiResponse<UnifiedPublication[]>>(
        `/publishing/all?${params.toString()}`
      );

      if (response.data?.success && response.data?.data) {
        return response.data.data;
      }

      return [];
    } catch (error: any) {
      console.error('Error al obtener publicaciones unificadas:', error);
      // No mostrar notificación aquí porque este método se llama frecuentemente
      return [];
    }
  }

  /**
   * Obtiene el resumen de publicaciones
   */
  async getPublishingSummary(): Promise<PublishingSummary> {
    try {
      const response = await apiClient.get<ApiResponse<PublishingSummary>>(
        '/publishing/summary'
      );

      if (response.data?.success && response.data?.data) {
        return response.data.data;
      }

      // Retornar resumen vacío si hay error
      return this.getEmptySummary();
    } catch (error: any) {
      console.error('Error al obtener resumen de publicaciones:', error);
      return this.getEmptySummary();
    }
  }

  /**
   * Inicia publicación remota para una cámara
   */
  async startRemotePublishing(
    cameraId: string, 
    serverId: number,
    options?: Partial<RemotePublishCommand>
  ): Promise<UnifiedPublication> {
    try {
      const payload: RemotePublishCommand = {
        server_id: serverId,
        ...options
      };

      const response = await apiClient.post<ApiResponse<UnifiedPublication>>(
        `/v1/cameras/${cameraId}/publish`,
        payload
      );

      if (response.data?.success && response.data?.data) {
        notificationStore.addNotification({
          type: 'success',
          title: 'Publicación iniciada',
          message: 'La cámara está siendo publicada al servidor remoto',
        });
        
        return response.data.data;
      }

      throw new Error('Error al iniciar publicación remota');
    } catch (error: any) {
      notificationStore.addNotification({
        type: 'error',
        title: 'Error al publicar',
        message: error.response?.data?.detail || 'No se pudo iniciar la publicación remota',
      });
      throw error;
    }
  }

  /**
   * Detiene publicación remota para una cámara
   */
  async stopRemotePublishing(cameraId: string, serverId: number): Promise<void> {
    try {
      const response = await apiClient.post<ApiResponse<void>>(
        `/v1/cameras/${cameraId}/unpublish`,
        { server_id: serverId }
      );

      if (response.data?.success) {
        notificationStore.addNotification({
          type: 'success',
          title: 'Publicación detenida',
          message: 'La publicación remota se detuvo correctamente',
        });
        return;
      }

      throw new Error('Error al detener publicación remota');
    } catch (error: any) {
      notificationStore.addNotification({
        type: 'error',
        title: 'Error al detener',
        message: error.response?.data?.detail || 'No se pudo detener la publicación remota',
      });
      throw error;
    }
  }

  /**
   * Inicia publicación local para una cámara
   * TODO: Implementar cuando el backend soporte publicación local unificada
   */
  async startLocalPublishing(cameraId: string): Promise<UnifiedPublication> {
    try {
      const response = await apiClient.post<ApiResponse<UnifiedPublication>>(
        '/publishing/start',
        { camera_id: cameraId }
      );

      if (response.data?.success && response.data?.data) {
        notificationStore.addNotification({
          type: 'success',
          title: 'Publicación local iniciada',
          message: 'La cámara está siendo publicada al servidor local',
        });
        
        return response.data.data;
      }

      throw new Error('Error al iniciar publicación local');
    } catch (error: any) {
      notificationStore.addNotification({
        type: 'error',
        title: 'Error al publicar',
        message: error.response?.data?.detail || 'No se pudo iniciar la publicación local',
      });
      throw error;
    }
  }

  /**
   * Detiene publicación local para una cámara
   * TODO: Implementar cuando el backend soporte publicación local unificada
   */
  async stopLocalPublishing(cameraId: string): Promise<void> {
    try {
      const response = await apiClient.post<ApiResponse<void>>(
        '/publishing/stop',
        { camera_id: cameraId }
      );

      if (response.data?.success) {
        notificationStore.addNotification({
          type: 'success',
          title: 'Publicación local detenida',
          message: 'La publicación local se detuvo correctamente',
        });
        return;
      }

      throw new Error('Error al detener publicación local');
    } catch (error: any) {
      notificationStore.addNotification({
        type: 'error',
        title: 'Error al detener',
        message: error.response?.data?.detail || 'No se pudo detener la publicación local',
      });
      throw error;
    }
  }

  /**
   * Reinicia una publicación (local o remota)
   */
  async restartPublication(
    cameraId: string, 
    type: PublicationType,
    serverId?: number
  ): Promise<UnifiedPublication> {
    try {
      if (type === 'remote' && serverId) {
        // Detener y reiniciar publicación remota
        await this.stopRemotePublishing(cameraId, serverId);
        await new Promise(resolve => setTimeout(resolve, 1000)); // Esperar 1 segundo
        return await this.startRemotePublishing(cameraId, serverId);
      } else {
        // Detener y reiniciar publicación local
        await this.stopLocalPublishing(cameraId);
        await new Promise(resolve => setTimeout(resolve, 1000)); // Esperar 1 segundo
        return await this.startLocalPublishing(cameraId);
      }
    } catch (error: any) {
      notificationStore.addNotification({
        type: 'error',
        title: 'Error al reiniciar',
        message: 'No se pudo reiniciar la publicación',
      });
      throw error;
    }
  }

  /**
   * Obtiene métricas detalladas de una publicación
   * TODO: Implementar cuando el backend proporcione endpoint específico
   */
  async getPublicationMetrics(
    cameraId: string,
    type: PublicationType,
    serverId?: number
  ): Promise<UnifiedPublication['metrics']> {
    try {
      // Por ahora, obtener todas las publicaciones y filtrar
      const publications = await this.getAllPublications();
      const publication = publications.find(p => 
        p.camera_id === cameraId && 
        p.publication_type === type &&
        (!serverId || p.server_id === serverId)
      );

      if (publication) {
        return publication.metrics;
      }

      // Retornar métricas vacías si no se encuentra
      return {
        fps: 0,
        bitrate_kbps: 0,
        viewers: 0,
        uptime_seconds: 0,
        latency_ms: 0,
      };
    } catch (error) {
      console.error('Error al obtener métricas:', error);
      return {
        fps: 0,
        bitrate_kbps: 0,
        viewers: 0,
        uptime_seconds: 0,
        latency_ms: 0,
      };
    }
  }

  /**
   * Retorna un resumen vacío para casos de error
   */
  private getEmptySummary(): PublishingSummary {
    return {
      total_publications: 0,
      local_publications: 0,
      remote_publications: 0,
      total_viewers: 0,
      total_servers: 0,
      active_servers: 0,
      total_bitrate_mbps: 0,
      average_fps: 0,
      servers_breakdown: [],
    };
  }
}

// Exportar instancia singleton
export const publishingUnifiedService = PublishingUnifiedService.getInstance();