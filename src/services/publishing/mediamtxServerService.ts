/**
 * Servicio para gestión de servidores MediaMTX remotos
 * Maneja el CRUD completo de configuraciones de servidores
 * 
 * @module services/publishing/mediamtxServerService
 */

import { apiClient } from '../api/apiClient';
import { notificationStore } from '../../stores/notificationStore';
import type { ApiResponse, PaginatedResponse } from '../../types/api.types';

// ====================================================================
// Types & Interfaces
// ====================================================================

/**
 * Representa un servidor MediaMTX remoto
 */
export interface MediaMTXServer {
  id: number;
  name: string;
  api_url: string;
  rtmp_url: string;
  rtsp_url: string;
  auth_required: boolean;
  is_authenticated: boolean;
  is_active: boolean;
  last_health_check: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * DTO para crear un nuevo servidor
 */
export interface CreateServerDto {
  name: string;
  api_url: string;
  rtmp_url: string;
  rtsp_url: string;
  auth_required: boolean;
  username?: string;
  password?: string;
}

/**
 * DTO para actualizar un servidor existente
 */
export interface UpdateServerDto {
  name?: string;
  api_url?: string;
  rtmp_url?: string;
  rtsp_url?: string;
  auth_required?: boolean;
  is_active?: boolean;
}

/**
 * Estado y métricas del servidor
 */
export interface ServerStatus {
  id: number;
  is_online: boolean;
  is_authenticated: boolean;
  active_publications: number;
  total_viewers: number;
  last_check: string;
  error_message?: string;
}

/**
 * Resultado de prueba de conexión
 */
export interface ConnectionTestResult {
  success: boolean;
  latency_ms: number;
  error?: string;
  api_reachable: boolean;
  rtmp_reachable: boolean;
  rtsp_reachable: boolean;
}

/**
 * Parámetros de filtrado para lista de servidores
 */
export interface ServerFilters {
  is_active?: boolean;
  is_authenticated?: boolean;
  search?: string;
}

// ====================================================================
// Service Implementation
// ====================================================================

/**
 * Servicio para gestión de servidores MediaMTX
 * Implementa el patrón singleton para mantener consistencia
 */
class MediaMTXServerService {
  private static instance: MediaMTXServerService;
  private readonly baseUrl = '/api/mediamtx/servers';
  
  // Cache interno para optimizar consultas frecuentes
  private serversCache: Map<number, MediaMTXServer> = new Map();
  private cacheTimestamp: number = 0;
  private readonly CACHE_DURATION = 30000; // 30 segundos

  private constructor() {}

  /**
   * Obtiene la instancia única del servicio
   */
  static getInstance(): MediaMTXServerService {
    if (!MediaMTXServerService.instance) {
      MediaMTXServerService.instance = new MediaMTXServerService();
    }
    return MediaMTXServerService.instance;
  }

  /**
   * Invalida el cache interno
   */
  private invalidateCache(): void {
    this.serversCache.clear();
    this.cacheTimestamp = 0;
  }

  /**
   * Verifica si el cache es válido
   */
  private isCacheValid(): boolean {
    return Date.now() - this.cacheTimestamp < this.CACHE_DURATION;
  }

  /**
   * Obtiene la lista paginada de servidores
   */
  async getServers(
    page: number = 1,
    pageSize: number = 10,
    filters?: ServerFilters
  ): Promise<PaginatedResponse<MediaMTXServer>> {
    try {
      // Construir parámetros de consulta
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });

      // Agregar filtros si existen
      if (filters?.is_active !== undefined) {
        params.append('is_active', filters.is_active.toString());
      }
      if (filters?.is_authenticated !== undefined) {
        params.append('is_authenticated', filters.is_authenticated.toString());
      }
      if (filters?.search) {
        params.append('search', filters.search);
      }

      const response = await apiClient.get<ApiResponse<PaginatedResponse<MediaMTXServer>>>(
        `${this.baseUrl}/?${params.toString()}`
      );

      if (response.data?.success && response.data?.data) {
        // Actualizar cache con los servidores obtenidos
        response.data.data.items.forEach((server: MediaMTXServer) => {
          this.serversCache.set(server.id, server);
        });
        this.cacheTimestamp = Date.now();
        
        return response.data!.data!;
      }

      throw new Error('Error al obtener la lista de servidores');
    } catch (error: any) {
      notificationStore.addNotification({
        type: 'error',
        title: 'Error al cargar servidores',
        message: error.response?.data?.detail || error.message,
      });
      throw error;
    }
  }

  /**
   * Obtiene un servidor por ID
   */
  async getServerById(id: number): Promise<MediaMTXServer> {
    try {
      // Verificar cache primero
      if (this.isCacheValid() && this.serversCache.has(id)) {
        return this.serversCache.get(id)!;
      }

      const response = await apiClient.get<ApiResponse<MediaMTXServer>>(
        `${this.baseUrl}/${id}`
      );

      if (response.data?.success && response.data?.data) {
        // Actualizar cache
        this.serversCache.set(id, response.data.data);
        return response.data!.data!;
      }

      throw new Error('Servidor no encontrado');
    } catch (error: any) {
      notificationStore.addNotification({
        type: 'error',
        title: 'Error al obtener servidor',
        message: error.response?.data?.detail || error.message,
      });
      throw error;
    }
  }

  /**
   * Crea un nuevo servidor
   */
  async createServer(data: CreateServerDto): Promise<MediaMTXServer> {
    try {
      const response = await apiClient.post<ApiResponse<MediaMTXServer>>(
        `${this.baseUrl}/`,
        data
      );

      if (response.data?.success && response.data?.data) {
        this.invalidateCache();
        
        notificationStore.addNotification({
          type: 'success',
          title: 'Servidor creado',
          message: `El servidor "${data.name}" se creó correctamente`,
        });
        
        return response.data!.data!;
      }

      throw new Error('Error al crear el servidor');
    } catch (error: any) {
      notificationStore.addNotification({
        type: 'error',
        title: 'Error al crear servidor',
        message: error.response?.data?.detail || error.message,
      });
      throw error;
    }
  }

  /**
   * Actualiza un servidor existente
   */
  async updateServer(id: number, data: UpdateServerDto): Promise<MediaMTXServer> {
    try {
      const response = await apiClient.put<ApiResponse<MediaMTXServer>>(
        `${this.baseUrl}/${id}`,
        data
      );

      if (response.data?.success && response.data?.data) {
        this.invalidateCache();
        
        notificationStore.addNotification({
          type: 'success',
          title: 'Servidor actualizado',
          message: 'Los cambios se guardaron correctamente',
        });
        
        return response.data!.data!;
      }

      throw new Error('Error al actualizar el servidor');
    } catch (error: any) {
      notificationStore.addNotification({
        type: 'error',
        title: 'Error al actualizar servidor',
        message: error.response?.data?.detail || error.message,
      });
      throw error;
    }
  }

  /**
   * Elimina un servidor
   */
  async deleteServer(id: number): Promise<void> {
    try {
      const response = await apiClient.delete<ApiResponse<void>>(
        `${this.baseUrl}/${id}`
      );

      if (response.data?.success) {
        this.invalidateCache();
        
        notificationStore.addNotification({
          type: 'success',
          title: 'Servidor eliminado',
          message: 'El servidor se eliminó correctamente',
        });
        
        return;
      }

      throw new Error('Error al eliminar el servidor');
    } catch (error: any) {
      notificationStore.addNotification({
        type: 'error',
        title: 'Error al eliminar servidor',
        message: error.response?.data?.detail || error.message,
      });
      throw error;
    }
  }

  /**
   * Obtiene el estado actual de un servidor
   */
  async getServerStatus(id: number): Promise<ServerStatus> {
    try {
      const response = await apiClient.get<ApiResponse<ServerStatus>>(
        `${this.baseUrl}/${id}/status`
      );

      if (response.data?.success && response.data?.data) {
        return response.data!.data!;
      }

      throw new Error('Error al obtener el estado del servidor');
    } catch (error: any) {
      // No mostrar notificación aquí ya que este método se llama frecuentemente
      throw error;
    }
  }

  /**
   * Prueba la conexión con un servidor
   */
  async testConnection(id: number): Promise<ConnectionTestResult> {
    try {
      const response = await apiClient.post<ApiResponse<ConnectionTestResult>>(
        `${this.baseUrl}/${id}/test`
      );

      if (response.data?.success && response.data?.data) {
        const result = response.data.data;
        
        if (result.success) {
          notificationStore.addNotification({
            type: 'success',
            title: 'Conexión exitosa',
            message: `Latencia: ${result.latency_ms}ms`,
          });
        } else {
          notificationStore.addNotification({
            type: 'warning',
            title: 'Conexión con problemas',
            message: result.error || 'Algunos servicios no están disponibles',
          });
        }
        
        return result;
      }

      throw new Error('Error al probar la conexión');
    } catch (error: any) {
      notificationStore.addNotification({
        type: 'error',
        title: 'Error al probar conexión',
        message: error.response?.data?.detail || error.message,
      });
      throw error;
    }
  }

  /**
   * Obtiene todos los servidores activos (sin paginación)
   * Útil para selectores y dropdowns
   */
  async getActiveServers(): Promise<MediaMTXServer[]> {
    try {
      // Usar un page_size grande para obtener todos los servidores activos
      const response = await this.getServers(1, 100, { is_active: true });
      return response.items;
    } catch (error) {
      console.error('Error al obtener servidores activos:', error);
      return [];
    }
  }

  /**
   * Obtiene servidores autenticados
   * Útil para publicación remota
   */
  async getAuthenticatedServers(): Promise<MediaMTXServer[]> {
    try {
      const response = await this.getServers(1, 100, { 
        is_active: true, 
        is_authenticated: true 
      });
      return response.items;
    } catch (error) {
      console.error('Error al obtener servidores autenticados:', error);
      return [];
    }
  }
}

// Exportar instancia singleton
export const mediamtxServerService = MediaMTXServerService.getInstance();