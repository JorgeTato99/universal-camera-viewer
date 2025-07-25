/**
 * Servicio de autenticación para servidores MediaMTX remotos
 * 
 * Gestiona la autenticación JWT con servidores MediaMTX remotos,
 * incluyendo login, logout, validación de tokens y estado de autenticación.
 */

import { apiClient } from '../api/apiClient';
import { notificationStore } from '../../stores/notificationStore';
import type { ApiResponse } from '../../types/api.types';

// ====================================================================
// Types & Interfaces
// ====================================================================

export interface LoginCredentials {
  server_id: number;
  username: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  server_id: number;
  server_name: string;
  message?: string;
  error?: string;
}

export interface AuthStatus {
  success: boolean;
  server_id?: number;
  server_name?: string;
  api_url?: string;
  is_authenticated?: boolean;
  last_check?: string;
  last_error?: string;
  error?: string;
}

export interface AllServersAuthStatus {
  success: boolean;
  servers?: AuthStatusServer[];
  authenticated_count?: number;
  total_count?: number;
  error?: string;
}

export interface AuthStatusServer {
  server_id: number;
  server_name: string;
  is_authenticated: boolean;
  last_check?: string;
  username?: string;
  expires_at?: string;
}

// ====================================================================
// Service Implementation
// ====================================================================

class MediaMTXAuthService {
  private static instance: MediaMTXAuthService;
  
  // Cache de estado de autenticación (se actualiza con polling o eventos)
  private authStatusCache: Map<number, AuthStatus> = new Map();
  
  private constructor() {}

  /**
   * Obtiene la instancia única del servicio
   */
  static getInstance(): MediaMTXAuthService {
    if (!MediaMTXAuthService.instance) {
      MediaMTXAuthService.instance = new MediaMTXAuthService();
    }
    return MediaMTXAuthService.instance;
  }

  /**
   * Autentica con un servidor MediaMTX remoto
   */
  async login(
    serverId: number,
    username: string,
    password: string
  ): Promise<LoginResponse> {
    try {
      const response = await apiClient.post<LoginResponse>(
        '/mediamtx/auth/login',
        {
          server_id: serverId,
          username,
          password,
        }
      );

      const result = response.data;

      if (!result) {
        return {
          success: false,
          server_id: serverId,
          server_name: '',
          error: 'Respuesta vacía del servidor',
        };
      }

      if (result.success) {
        // Actualizar cache
        this.updateAuthCache(serverId, {
          success: true,
          server_id: serverId,
          server_name: result.server_name,
          is_authenticated: true,
          last_check: new Date().toISOString(),
        });

        notificationStore.addNotification({
          type: 'success',
          title: 'Autenticación exitosa',
          message: `Conectado a ${result.server_name}`,
        });

        return result;
      }

      return {
        success: false,
        server_id: serverId,
        server_name: '',
        error: result.error || 'Error de autenticación',
      };
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.message || 'Error de conexión';
      
      notificationStore.addNotification({
        type: 'error',
        title: 'Error de autenticación',
        message: errorMsg,
      });

      return {
        success: false,
        server_id: serverId,
        server_name: '',
        error: errorMsg,
      };
    }
  }

  /**
   * Cierra sesión con un servidor
   */
  async logout(serverId: number): Promise<boolean> {
    try {
      const response = await apiClient.post<LoginResponse>(
        '/mediamtx/auth/logout',
        { server_id: serverId }
      );

      if (response.data?.success) {
        // Limpiar cache
        this.authStatusCache.delete(serverId);

        notificationStore.addNotification({
          type: 'info',
          title: 'Sesión cerrada',
          message: 'Se cerró la sesión con el servidor remoto',
        });

        return true;
      }

      return false;
    } catch (error: any) {
      console.error('Error al cerrar sesión:', error);
      return false;
    }
  }

  /**
   * Obtiene el estado de autenticación de un servidor
   */
  async getAuthStatus(serverId: number): Promise<AuthStatus> {
    try {
      // Primero verificar cache
      const cached = this.authStatusCache.get(serverId);
      if (cached && this.isCacheValid(cached)) {
        return cached;
      }

      const response = await apiClient.get<ApiResponse<AuthStatus>>(
        `/mediamtx/auth/status/${serverId}`
      );

      if (response.data?.success && response.data?.data) {
        const status = response.data.data;
        
        // Actualizar cache
        this.updateAuthCache(serverId, status);
        
        return status;
      }

      return {
        success: false,
        server_id: serverId,
        is_authenticated: false,
        error: 'No se pudo obtener el estado',
      };
    } catch (error: any) {
      return {
        success: false,
        server_id: serverId,
        is_authenticated: false,
        error: error.message || 'Error de conexión',
      };
    }
  }

  /**
   * Obtiene el estado de autenticación de todos los servidores
   */
  async getAllAuthStatus(): Promise<AllServersAuthStatus> {
    try {
      const response = await apiClient.get<ApiResponse<AllServersAuthStatus>>(
        '/mediamtx/auth/status'
      );

      if (response.data?.success && response.data?.data) {
        const allStatus = response.data.data;
        
        // Actualizar cache con todos los estados
        allStatus.servers?.forEach(server => {
          this.updateAuthCache(server.server_id, {
            success: true,
            server_id: server.server_id,
            server_name: server.server_name,
            is_authenticated: server.is_authenticated,
            last_check: server.last_check,
          });
        });
        
        return allStatus;
      }

      return {
        success: false,
        servers: [],
        authenticated_count: 0,
        total_count: 0,
      };
    } catch (error: any) {
      console.error('Error obteniendo estado de autenticación:', error);
      return {
        success: false,
        servers: [],
        authenticated_count: 0,
        total_count: 0,
        error: error.message,
      };
    }
  }

  /**
   * Valida la conexión con un servidor (prueba el token si existe)
   */
  async validateConnection(serverId: number): Promise<{
    success: boolean;
    message: string;
    authRequired: boolean;
    isAuthenticated: boolean;
  }> {
    try {
      const response = await apiClient.post<ApiResponse<any>>(
        `/mediamtx/servers/${serverId}/test-connection`
      );

      if (response.data?.success && response.data?.data) {
        const result = response.data.data;
        
        return {
          success: result.success,
          message: result.message,
          authRequired: result.details?.auth_required || false,
          isAuthenticated: result.details?.auth_status?.includes('Autenticado') || false,
        };
      }

      return {
        success: false,
        message: 'Error al probar conexión',
        authRequired: false,
        isAuthenticated: false,
      };
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || 'Error de conexión',
        authRequired: false,
        isAuthenticated: false,
      };
    }
  }

  /**
   * Limpia el cache de autenticación
   */
  clearCache(): void {
    this.authStatusCache.clear();
  }

  /**
   * Obtiene el estado de autenticación desde el cache
   */
  getCachedAuthStatus(serverId: number): AuthStatus | undefined {
    return this.authStatusCache.get(serverId);
  }

  /**
   * Actualiza el cache de autenticación
   */
  private updateAuthCache(serverId: number, status: AuthStatus): void {
    this.authStatusCache.set(serverId, {
      ...status,
      last_check: status.last_check || new Date().toISOString(),
    });
  }

  /**
   * Verifica si el cache es válido (menos de 5 minutos)
   */
  private isCacheValid(cached: AuthStatus): boolean {
    if (!cached.last_check) return false;
    
    const lastCheck = new Date(cached.last_check);
    const now = new Date();
    const diffMinutes = (now.getTime() - lastCheck.getTime()) / (1000 * 60);
    
    return diffMinutes < 5;
  }
}

// Exportar instancia singleton
export const mediamtxAuthService = MediaMTXAuthService.getInstance();