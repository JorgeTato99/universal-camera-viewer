/**
 * 🔐 MediaMTX Auth Hook - Universal Camera Viewer
 * Hook personalizado para gestión de autenticación con servidores MediaMTX
 * 
 * Proporciona:
 * - Estado de autenticación por servidor
 * - Acciones de login/logout
 * - Validación de conexión
 * - Lista de servidores autenticados
 */

import { useState, useCallback, useEffect } from 'react';
import { 
  mediamtxRemoteService,
  MediaMTXServer,
  AuthStatus 
} from '../../../services/publishing/mediamtxRemoteService';

interface UseMediaMTXAuthReturn {
  // Estado
  servers: MediaMTXServer[];
  authStatuses: Map<number, AuthStatus>;
  isLoading: boolean;
  isAuthenticating: Map<number, boolean>;
  
  // Acciones
  authenticate: (serverId: number, username: string, password: string) => Promise<boolean>;
  logout: (serverId: number) => Promise<void>;
  validateConnection: (serverId: number) => Promise<boolean>;
  refreshAuthStatus: (serverId?: number) => Promise<void>;
  
  // Utilidades
  getAuthenticatedServers: () => MediaMTXServer[];
  isAuthenticated: (serverId: number) => boolean;
  getAuthError: (serverId: number) => string | undefined;
}

/**
 * Hook para gestión de autenticación MediaMTX
 */
export function useMediaMTXAuth(): UseMediaMTXAuthReturn {
  // Estado local
  const [servers, setServers] = useState<MediaMTXServer[]>([]);
  const [authStatuses, setAuthStatuses] = useState<Map<number, AuthStatus>>(new Map());
  const [isLoading, setIsLoading] = useState(false);
  const [isAuthenticating, setIsAuthenticating] = useState<Map<number, boolean>>(new Map());
  
  // Cargar servidores
  const loadServers = useCallback(async () => {
    setIsLoading(true);
    try {
      // TODO: Implementar carga real de servidores desde endpoint /api/mediamtx/servers
      // Por ahora, incluir servidor de producción real
      const mockServers: MediaMTXServer[] = [
        {
          id: 1,
          name: 'MediaMTX Production Server',
          url: 'rtsp://31.220.104.212:8554',
          api_url: 'http://31.220.104.212:8000',
          username: 'jorge.cliente'
        },
        {
          id: 2,
          name: 'MediaMTX Local Dev',
          url: 'rtsp://localhost:8554',
          api_url: 'http://localhost:9997',
          username: 'admin'
        }
      ];
      
      setServers(mockServers);
      
      // Cargar estados de autenticación
      await refreshAuthStatus();
    } catch (error) {
      console.error('Error cargando servidores:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  // Autenticar servidor
  const authenticate = useCallback(async (
    serverId: number,
    username: string,
    password: string
  ): Promise<boolean> => {
    setIsAuthenticating(prev => new Map(prev).set(serverId, true));
    
    try {
      const response = await mediamtxRemoteService.authenticate({
        server_id: serverId,
        username,
        password
      });
      
      if (response.success && response.data) {
        // Actualizar estado de autenticación
        setAuthStatuses(prev => new Map(prev).set(serverId, response.data!));
        
        // Actualizar servidor
        setServers(prev => prev.map(server =>
          server.id === serverId
            ? { ...server, is_authenticated: true, username }
            : server
        ));
        
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Error autenticando:', error);
      return false;
    } finally {
      setIsAuthenticating(prev => {
        const newMap = new Map(prev);
        newMap.delete(serverId);
        return newMap;
      });
    }
  }, []);
  
  // Cerrar sesión
  const logout = useCallback(async (serverId: number) => {
    try {
      await mediamtxRemoteService.logout(serverId);
      
      // Limpiar estado local
      setAuthStatuses(prev => {
        const newMap = new Map(prev);
        newMap.delete(serverId);
        return newMap;
      });
      
      // Actualizar servidor
      setServers(prev => prev.map(server =>
        server.id === serverId
          ? { ...server, is_authenticated: false }
          : server
      ));
    } catch (error) {
      console.error('Error cerrando sesión:', error);
    }
  }, []);
  
  // Validar conexión
  const validateConnection = useCallback(async (serverId: number): Promise<boolean> => {
    try {
      const response = await mediamtxRemoteService.validateConnection(serverId);
      
      if (response.success && response.data) {
        setAuthStatuses(prev => new Map(prev).set(serverId, response.data!));
        return response.data.is_authenticated;
      }
      
      return false;
    } catch (error) {
      console.error('Error validando conexión:', error);
      return false;
    }
  }, []);
  
  // Refrescar estado de autenticación
  const refreshAuthStatus = useCallback(async (serverId?: number) => {
    try {
      const response = await mediamtxRemoteService.getAuthStatus(serverId);
      
      if (response.success && response.data) {
        if (Array.isArray(response.data)) {
          // Múltiples estados
          const newStatuses = new Map<number, AuthStatus>();
          response.data.forEach(status => {
            newStatuses.set(status.server_id, status);
          });
          setAuthStatuses(newStatuses);
        } else {
          // Estado único
          setAuthStatuses(prev => new Map(prev).set(response.data.server_id, response.data));
        }
      }
    } catch (error) {
      console.error('Error refrescando estado de autenticación:', error);
    }
  }, []);
  
  // Obtener servidores autenticados
  const getAuthenticatedServers = useCallback(() => {
    return servers.filter(server => {
      const authStatus = authStatuses.get(server.id);
      return authStatus?.is_authenticated;
    });
  }, [servers, authStatuses]);
  
  // Verificar si un servidor está autenticado
  const isAuthenticated = useCallback((serverId: number): boolean => {
    const authStatus = authStatuses.get(serverId);
    return authStatus?.is_authenticated || false;
  }, [authStatuses]);
  
  // Obtener error de autenticación
  const getAuthError = useCallback((serverId: number): string | undefined => {
    const authStatus = authStatuses.get(serverId);
    return authStatus?.error;
  }, [authStatuses]);
  
  // Cargar servidores al montar
  useEffect(() => {
    loadServers();
  }, [loadServers]);
  
  // Actualizar cache del servicio cuando cambian los estados
  useEffect(() => {
    // Sincronizar con el cache del servicio
    authStatuses.forEach((status, serverId) => {
      const cached = mediamtxRemoteService.getCachedAuthStatus(serverId);
      if (!cached || cached.last_check < status.last_check) {
        // El estado local es más reciente, no hacer nada
        // (el servicio ya tiene el estado actualizado)
      }
    });
  }, [authStatuses]);
  
  return {
    // Estado
    servers,
    authStatuses,
    isLoading,
    isAuthenticating,
    
    // Acciones
    authenticate,
    logout,
    validateConnection,
    refreshAuthStatus,
    
    // Utilidades
    getAuthenticatedServers,
    isAuthenticated,
    getAuthError
  };
}