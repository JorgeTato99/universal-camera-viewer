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

import { useCallback, useEffect } from 'react';
import { usePublishingStore } from '../../../stores/publishingStore';
import { 
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
 * Conecta con el publishingStore para estado centralizado
 */
export function useMediaMTXAuth(): UseMediaMTXAuthReturn {
  // Obtener estado y acciones del store
  const servers = usePublishingStore((state) => state.remote.servers);
  const authStatuses = usePublishingStore((state) => state.remote.authStatuses);
  const isLoadingServers = usePublishingStore((state) => state.remote.isLoadingServers);
  const isLoadingAuth = usePublishingStore((state) => state.remote.isLoadingAuth);
  
  const fetchRemoteServers = usePublishingStore((state) => state.fetchRemoteServers);
  const authenticateServer = usePublishingStore((state) => state.authenticateServer);
  const logoutServer = usePublishingStore((state) => state.logoutServer);
  const isServerAuthenticated = usePublishingStore((state) => state.isServerAuthenticated);
  const getAuthenticatedServers = usePublishingStore((state) => state.getAuthenticatedServers);
  
  // Autenticar servidor (usa store)
  const authenticate = useCallback(async (
    serverId: number,
    username: string,
    password: string
  ): Promise<boolean> => {
    return await authenticateServer(serverId, username, password);
  }, [authenticateServer]);
  
  // Cerrar sesión (usa store)
  const logout = useCallback(async (serverId: number) => {
    await logoutServer(serverId);
  }, [logoutServer]);
  
  // Validar conexión
  const validateConnection = useCallback(async (serverId: number): Promise<boolean> => {
    // TODO: Implementar validación real conectada con el store
    // Por ahora verificar el estado de autenticación local
    return isServerAuthenticated(serverId);
  }, [isServerAuthenticated]);
  
  // Refrescar estado de autenticación
  const refreshAuthStatus = useCallback(async (serverId?: number) => {
    // TODO: Implementar refresh real de estado de autenticación
    // Esto debería ser manejado por el store con polling o WebSocket
    console.log('Refreshing auth status for server:', serverId);
  }, []);
  
  // Verificar si un servidor está autenticado (usa store)
  const isAuthenticated = useCallback((serverId: number): boolean => {
    return isServerAuthenticated(serverId);
  }, [isServerAuthenticated]);
  
  // Obtener error de autenticación
  const getAuthError = useCallback((serverId: number): string | undefined => {
    const authStatus = authStatuses.get(serverId);
    return authStatus?.error;
  }, [authStatuses]);
  
  // Cargar servidores al montar
  useEffect(() => {
    // Solo cargar si no hay servidores
    if (servers.length === 0 && !isLoadingServers) {
      fetchRemoteServers();
    }
  }, [servers.length, isLoadingServers, fetchRemoteServers]);
  
  return {
    // Estado
    servers,
    authStatuses,
    isLoading: isLoadingServers,
    isAuthenticating: isLoadingAuth,
    
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