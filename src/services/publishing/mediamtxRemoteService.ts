/**
 * 🌐 MediaMTX Remote Service - Universal Camera Viewer
 * Servicio para gestión de publicaciones a servidores MediaMTX remotos
 * 
 * Este servicio maneja:
 * - Autenticación con servidores remotos
 * - Publicación de cámaras locales a servidores remotos
 * - Gestión del ciclo de vida de streams remotos
 * - Monitoreo de estado y métricas
 */

import { apiClient } from '../api/apiClient';
import { publishingService } from './publishingService';
import { notificationStore } from '../../stores/notificationStore';
import {
  ApiResponse,
  PublishStatus,
  PublishMetrics,
  PublishingStatus
} from '../../features/publishing/types';

// === TIPOS ESPECÍFICOS PARA MEDIAMTX REMOTO ===

/**
 * Información de servidor MediaMTX remoto
 */
export interface MediaMTXServer {
  id: number;
  name: string;
  url: string;
  api_url?: string;
  username?: string;
  // password se maneja solo en backend por seguridad
  is_authenticated?: boolean;
  last_auth_check?: string;
}

/**
 * Estado de autenticación
 */
export interface AuthStatus {
  server_id: number;
  is_authenticated: boolean;
  token_expires_at?: string;
  last_check: string;
  error?: string;
}

/**
 * Request para autenticación
 */
export interface AuthRequest {
  server_id: number;
  username: string;
  password: string;
}

/**
 * Estado de publicación remota
 */
export interface RemotePublishStatus extends PublishStatus {
  server_id: number;
  server_name: string;
  remote_camera_id?: string;
  publish_url?: string;
  webrtc_url?: string;
  is_remote: boolean;
}

/**
 * Request para publicación remota
 */
export interface RemotePublishRequest {
  camera_id: string;
  server_id: number;
  custom_name?: string;
  custom_description?: string;
}

/**
 * Métricas de publicación remota
 */
export interface RemotePublishMetrics extends PublishMetrics {
  server_latency_ms?: number;
  remote_viewers?: number;
  bandwidth_usage_mbps?: number;
}

// === SERVICIO PRINCIPAL ===

/**
 * Servicio para gestión de publicaciones MediaMTX remotas
 */
class MediaMTXRemoteService {
  private baseEndpoint = '/mediamtx';
  
  // Cache de estado de autenticación
  private authStatusCache = new Map<number, AuthStatus>();
  
  // Cache de publicaciones remotas activas
  private remotePublications = new Map<string, RemotePublishStatus>();

  // === AUTENTICACIÓN ===

  /**
   * Autenticar con servidor MediaMTX remoto
   */
  async authenticate(request: AuthRequest): Promise<ApiResponse<AuthStatus>> {
    try {
      const response = await apiClient.post<AuthStatus>(
        `${this.baseEndpoint}/auth/login`,
        request
      );
      
      if (response.success && response.data) {
        // Cachear estado de autenticación
        this.authStatusCache.set(request.server_id, response.data);
        
        notificationStore.showSuccess(
          'Autenticación exitosa',
          `Conectado al servidor MediaMTX #${request.server_id}`
        );
      }
      
      return response;
    } catch (error) {
      notificationStore.showError(
        'Error de autenticación',
        'No se pudo autenticar con el servidor MediaMTX'
      );
      throw error;
    }
  }

  /**
   * Cerrar sesión de servidor MediaMTX
   */
  async logout(serverId: number): Promise<ApiResponse<{ message: string }>> {
    try {
      const response = await apiClient.post<{ message: string }>(
        `${this.baseEndpoint}/auth/logout`,
        { server_id: serverId }
      );
      
      if (response.success) {
        // Limpiar cache
        this.authStatusCache.delete(serverId);
        
        // Limpiar publicaciones de este servidor
        this.remotePublications.forEach((pub, cameraId) => {
          if (pub.server_id === serverId) {
            this.remotePublications.delete(cameraId);
          }
        });
      }
      
      return response;
    } catch (error) {
      console.error('Error al cerrar sesión:', error);
      throw error;
    }
  }

  /**
   * Obtener estado de autenticación
   */
  async getAuthStatus(serverId?: number): Promise<ApiResponse<AuthStatus | AuthStatus[]>> {
    const endpoint = serverId 
      ? `${this.baseEndpoint}/auth/status/${serverId}`
      : `${this.baseEndpoint}/auth/status`;
      
    return apiClient.get<AuthStatus | AuthStatus[]>(endpoint);
  }

  /**
   * Validar conexión con servidor
   */
  async validateConnection(serverId: number): Promise<ApiResponse<AuthStatus>> {
    try {
      const response = await apiClient.post<AuthStatus>(
        `${this.baseEndpoint}/auth/validate/${serverId}`
      );
      
      if (response.success && response.data) {
        // Actualizar cache
        this.authStatusCache.set(serverId, response.data);
      }
      
      return response;
    } catch (error) {
      console.error('Error validando conexión:', error);
      throw error;
    }
  }

  // === PUBLICACIÓN REMOTA ===

  /**
   * Iniciar publicación a servidor remoto
   */
  async startRemotePublishing(request: RemotePublishRequest): Promise<ApiResponse<RemotePublishStatus>> {
    try {
      // Verificar autenticación primero
      const authStatus = this.authStatusCache.get(request.server_id);
      if (!authStatus?.is_authenticated) {
        throw new Error('Servidor no autenticado. Por favor, autentique primero.');
      }
      
      // Iniciar publicación remota
      const response = await apiClient.post<RemotePublishStatus>(
        `${this.baseEndpoint}/remote-publishing/start`,
        request
      );
      
      if (response.success && response.data) {
        // Cachear publicación remota
        this.remotePublications.set(request.camera_id, response.data);
        
        notificationStore.showSuccess(
          'Publicación remota iniciada',
          `Streaming activo hacia servidor remoto`
        );
      }
      
      return response;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Error desconocido';
      notificationStore.showError(
        'Error al iniciar publicación remota',
        errorMessage
      );
      throw error;
    }
  }

  /**
   * Detener publicación remota
   */
  async stopRemotePublishing(cameraId: string): Promise<ApiResponse<{ message: string }>> {
    try {
      const response = await apiClient.post<{ message: string }>(
        `${this.baseEndpoint}/remote-publishing/stop`,
        { camera_id: cameraId }
      );
      
      if (response.success) {
        // Limpiar cache
        this.remotePublications.delete(cameraId);
        
        notificationStore.showInfo(
          'Publicación remota detenida',
          'Se detuvo el streaming hacia el servidor remoto'
        );
      }
      
      return response;
    } catch (error) {
      console.error('Error al detener publicación remota:', error);
      throw error;
    }
  }

  /**
   * Obtener estado de publicación remota
   */
  async getRemotePublishingStatus(cameraId: string): Promise<ApiResponse<RemotePublishStatus>> {
    try {
      const response = await apiClient.get<RemotePublishStatus>(
        `${this.baseEndpoint}/remote-publishing/status/${cameraId}`
      );
      
      if (response.success && response.data) {
        // Actualizar cache
        this.remotePublications.set(cameraId, response.data);
      }
      
      return response;
    } catch (error) {
      // Si es 404, la publicación no existe
      if (error instanceof Error && error.message.includes('404')) {
        this.remotePublications.delete(cameraId);
      }
      throw error;
    }
  }

  /**
   * Listar todas las publicaciones remotas activas
   */
  async listRemotePublications(): Promise<ApiResponse<RemotePublishStatus[]>> {
    try {
      const response = await apiClient.get<RemotePublishStatus[]>(
        `${this.baseEndpoint}/remote-publishing/list`
      );
      
      if (response.success && response.data) {
        // Actualizar cache completo
        this.remotePublications.clear();
        response.data.forEach(pub => {
          this.remotePublications.set(pub.camera_id, pub);
        });
      }
      
      return response;
    } catch (error) {
      console.error('Error listando publicaciones remotas:', error);
      throw error;
    }
  }

  /**
   * Reiniciar publicación remota
   */
  async restartRemotePublishing(cameraId: string): Promise<ApiResponse<RemotePublishStatus>> {
    try {
      const response = await apiClient.post<RemotePublishStatus>(
        `${this.baseEndpoint}/remote-publishing/restart/${cameraId}`
      );
      
      if (response.success && response.data) {
        // Actualizar cache
        this.remotePublications.set(cameraId, response.data);
        
        notificationStore.showInfo(
          'Publicación reiniciada',
          'Se reinició el streaming hacia el servidor remoto'
        );
      }
      
      return response;
    } catch (error) {
      console.error('Error al reiniciar publicación remota:', error);
      throw error;
    }
  }

  /**
   * Obtener health check del sistema remoto
   */
  async getRemoteHealth(): Promise<ApiResponse<{
    healthy: boolean;
    active_publications: number;
    authenticated_servers: number;
    issues: string[];
  }>> {
    return apiClient.get(`${this.baseEndpoint}/remote-publishing/health`);
  }

  // === MÉTODOS DE UTILIDAD ===

  /**
   * Verificar si una cámara está publicando remotamente
   */
  isPublishingRemotely(cameraId: string): boolean {
    const publication = this.remotePublications.get(cameraId);
    return publication?.status === PublishingStatus.PUBLISHING;
  }

  /**
   * Obtener publicación remota desde cache
   */
  getCachedRemotePublication(cameraId: string): RemotePublishStatus | undefined {
    return this.remotePublications.get(cameraId);
  }

  /**
   * Obtener estado de autenticación desde cache
   */
  getCachedAuthStatus(serverId: number): AuthStatus | undefined {
    return this.authStatusCache.get(serverId);
  }

  /**
   * Limpiar todos los caches
   */
  clearCache(): void {
    this.authStatusCache.clear();
    this.remotePublications.clear();
  }

  /**
   * Obtener resumen de publicaciones remotas
   */
  getRemotePublicationsSummary(): {
    total: number;
    publishing: number;
    error: number;
    byServer: Map<number, number>;
  } {
    const publications = Array.from(this.remotePublications.values());
    const byServer = new Map<number, number>();
    
    let publishing = 0;
    let error = 0;
    
    publications.forEach(pub => {
      // Contar por estado
      if (pub.status === PublishingStatus.PUBLISHING) publishing++;
      if (pub.status === PublishingStatus.ERROR) error++;
      
      // Contar por servidor
      const count = byServer.get(pub.server_id) || 0;
      byServer.set(pub.server_id, count + 1);
    });
    
    return {
      total: publications.length,
      publishing,
      error,
      byServer
    };
  }
}

// Instancia singleton del servicio
export const mediamtxRemoteService = new MediaMTXRemoteService();

// Exportar tipos para uso en otros módulos
export type {
  MediaMTXServer,
  AuthStatus,
  AuthRequest,
  RemotePublishStatus,
  RemotePublishRequest,
  RemotePublishMetrics
};