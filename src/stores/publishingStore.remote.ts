/**
 * 🌐 Publishing Store Remote Extension - Universal Camera Viewer
 * Extensión del store de publicación para servidores MediaMTX remotos
 * 
 * Esta extensión agrega funcionalidad para:
 * - Gestión de servidores MediaMTX remotos
 * - Autenticación con servidores
 * - Publicación remota de cámaras
 * - Monitoreo de estado remoto
 */

import { StateCreator } from 'zustand';
import { 
  mediamtxRemoteService,
  MediaMTXServer,
  AuthStatus,
  RemotePublishStatus,
  RemotePublishRequest
} from '../services/publishing/mediamtxRemoteService';
import { notificationStore } from './notificationStore';

// === TIPOS ===

export interface RemotePublishingState {
  // === ESTADO REMOTO ===
  
  // Servidores MediaMTX remotos
  remoteServers: MediaMTXServer[];
  
  // Estado de autenticación por servidor
  authStatuses: Map<number, AuthStatus>;
  
  // Publicaciones remotas activas
  remotePublications: Map<string, RemotePublishStatus>;
  
  // Estados de carga específicos
  isAuthenticating: Map<number, boolean>;
  isLoadingRemoteServers: boolean;
  
  // === ACCIONES REMOTAS ===
  
  // Gestión de servidores
  fetchRemoteServers: () => Promise<void>;
  addRemoteServer: (server: Partial<MediaMTXServer>) => Promise<void>;
  updateRemoteServer: (serverId: number, updates: Partial<MediaMTXServer>) => Promise<void>;
  deleteRemoteServer: (serverId: number) => Promise<void>;
  
  // Autenticación
  authenticateServer: (serverId: number, username: string, password: string) => Promise<boolean>;
  logoutServer: (serverId: number) => Promise<void>;
  refreshAuthStatus: (serverId?: number) => Promise<void>;
  
  // Publicación remota
  startRemotePublishing: (cameraId: string, serverId: number, customName?: string) => Promise<void>;
  stopRemotePublishing: (cameraId: string) => Promise<void>;
  restartRemotePublishing: (cameraId: string) => Promise<void>;
  
  // Obtener estado
  fetchRemotePublications: () => Promise<void>;
  fetchRemotePublicationStatus: (cameraId: string) => Promise<void>;
  
  // === SELECTORES REMOTOS ===
  
  getAuthenticatedServers: () => MediaMTXServer[];
  getRemotePublicationByCameraId: (cameraId: string) => RemotePublishStatus | undefined;
  isPublishingRemotely: (cameraId: string) => boolean;
  getRemotePublicationCounts: () => {
    total: number;
    publishing: number;
    error: number;
    byServer: Map<number, number>;
  };
}

// === SLICE CREATOR ===

export const createRemotePublishingSlice: StateCreator<
  RemotePublishingState,
  [],
  [],
  RemotePublishingState
> = (set, get) => ({
  // === ESTADO INICIAL ===
  
  remoteServers: [],
  authStatuses: new Map(),
  remotePublications: new Map(),
  isAuthenticating: new Map(),
  isLoadingRemoteServers: false,
  
  // === IMPLEMENTACIÓN DE ACCIONES ===
  
  // Gestión de servidores
  fetchRemoteServers: async () => {
    set({ isLoadingRemoteServers: true });
    
    try {
      // TODO: Implementar endpoint para obtener servidores remotos
      // Por ahora, usar datos mock
      const mockServers: MediaMTXServer[] = [
        {
          id: 1,
          name: 'MediaMTX Cloud',
          url: 'rtsp://cloud.mediamtx.com:8554',
          api_url: 'https://cloud.mediamtx.com/api',
          username: 'demo',
          is_authenticated: false
        }
      ];
      
      set({ 
        remoteServers: mockServers,
        isLoadingRemoteServers: false 
      });
    } catch (error) {
      console.error('Error obteniendo servidores remotos:', error);
      set({ isLoadingRemoteServers: false });
    }
  },
  
  addRemoteServer: async (server) => {
    // TODO: Implementar endpoint para agregar servidor
    const newServer: MediaMTXServer = {
      id: Date.now(), // ID temporal
      name: server.name || 'Nuevo servidor',
      url: server.url || '',
      api_url: server.api_url,
      username: server.username,
      is_authenticated: false,
      ...server
    };
    
    set(state => ({
      remoteServers: [...state.remoteServers, newServer]
    }));
    
    notificationStore.showSuccess(
      'Servidor agregado',
      `Servidor "${newServer.name}" agregado exitosamente`
    );
  },
  
  updateRemoteServer: async (serverId, updates) => {
    set(state => ({
      remoteServers: state.remoteServers.map(server =>
        server.id === serverId ? { ...server, ...updates } : server
      )
    }));
  },
  
  deleteRemoteServer: async (serverId) => {
    // Cerrar sesión primero si está autenticado
    const authStatus = get().authStatuses.get(serverId);
    if (authStatus?.is_authenticated) {
      await get().logoutServer(serverId);
    }
    
    set(state => ({
      remoteServers: state.remoteServers.filter(s => s.id !== serverId),
      authStatuses: new Map(Array.from(state.authStatuses).filter(([id]) => id !== serverId))
    }));
    
    notificationStore.showInfo('Servidor eliminado', 'Servidor eliminado exitosamente');
  },
  
  // Autenticación
  authenticateServer: async (serverId, username, password) => {
    set(state => ({
      isAuthenticating: new Map(state.isAuthenticating).set(serverId, true)
    }));
    
    try {
      const response = await mediamtxRemoteService.authenticate({
        server_id: serverId,
        username,
        password
      });
      
      if (response.success && response.data) {
        // Actualizar estado de autenticación
        set(state => ({
          authStatuses: new Map(state.authStatuses).set(serverId, response.data!),
          remoteServers: state.remoteServers.map(server =>
            server.id === serverId 
              ? { ...server, is_authenticated: true, username }
              : server
          )
        }));
        
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Error autenticando servidor:', error);
      return false;
    } finally {
      set(state => ({
        isAuthenticating: new Map(state.isAuthenticating).set(serverId, false)
      }));
    }
  },
  
  logoutServer: async (serverId) => {
    try {
      await mediamtxRemoteService.logout(serverId);
      
      // Limpiar estado local
      set(state => ({
        authStatuses: new Map(Array.from(state.authStatuses).filter(([id]) => id !== serverId)),
        remoteServers: state.remoteServers.map(server =>
          server.id === serverId 
            ? { ...server, is_authenticated: false }
            : server
        ),
        // Limpiar publicaciones de este servidor
        remotePublications: new Map(
          Array.from(state.remotePublications).filter(([_, pub]) => pub.server_id !== serverId)
        )
      }));
      
      notificationStore.showInfo('Sesión cerrada', 'Se cerró la sesión del servidor');
    } catch (error) {
      console.error('Error cerrando sesión:', error);
    }
  },
  
  refreshAuthStatus: async (serverId) => {
    try {
      const response = await mediamtxRemoteService.getAuthStatus(serverId);
      
      if (response.success && response.data) {
        if (Array.isArray(response.data)) {
          // Múltiples estados
          const newStatuses = new Map(get().authStatuses);
          response.data.forEach(status => {
            newStatuses.set(status.server_id, status);
          });
          set({ authStatuses: newStatuses });
        } else {
          // Estado único
          set(state => ({
            authStatuses: new Map(state.authStatuses).set(response.data.server_id, response.data)
          }));
        }
      }
    } catch (error) {
      console.error('Error actualizando estado de autenticación:', error);
    }
  },
  
  // Publicación remota
  startRemotePublishing: async (cameraId, serverId, customName) => {
    try {
      const response = await mediamtxRemoteService.startRemotePublishing({
        camera_id: cameraId,
        server_id: serverId,
        custom_name: customName
      });
      
      if (response.success && response.data) {
        set(state => ({
          remotePublications: new Map(state.remotePublications).set(cameraId, response.data!)
        }));
      } else {
        throw new Error(response.error || 'Error al iniciar publicación remota');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Error desconocido';
      notificationStore.showError('Error al publicar', errorMessage);
      throw error;
    }
  },
  
  stopRemotePublishing: async (cameraId) => {
    try {
      await mediamtxRemoteService.stopRemotePublishing(cameraId);
      
      set(state => {
        const newPublications = new Map(state.remotePublications);
        newPublications.delete(cameraId);
        return { remotePublications: newPublications };
      });
    } catch (error) {
      console.error('Error deteniendo publicación remota:', error);
      throw error;
    }
  },
  
  restartRemotePublishing: async (cameraId) => {
    try {
      const response = await mediamtxRemoteService.restartRemotePublishing(cameraId);
      
      if (response.success && response.data) {
        set(state => ({
          remotePublications: new Map(state.remotePublications).set(cameraId, response.data!)
        }));
      }
    } catch (error) {
      console.error('Error reiniciando publicación remota:', error);
      throw error;
    }
  },
  
  // Obtener estado
  fetchRemotePublications: async () => {
    try {
      const response = await mediamtxRemoteService.listRemotePublications();
      
      if (response.success && response.data) {
        const newPublications = new Map<string, RemotePublishStatus>();
        response.data.forEach(pub => {
          newPublications.set(pub.camera_id, pub);
        });
        
        set({ remotePublications: newPublications });
      }
    } catch (error) {
      console.error('Error obteniendo publicaciones remotas:', error);
    }
  },
  
  fetchRemotePublicationStatus: async (cameraId) => {
    try {
      const response = await mediamtxRemoteService.getRemotePublishingStatus(cameraId);
      
      if (response.success && response.data) {
        set(state => ({
          remotePublications: new Map(state.remotePublications).set(cameraId, response.data!)
        }));
      }
    } catch (error) {
      // Si es 404, eliminar de la lista
      if (error instanceof Error && error.message.includes('404')) {
        set(state => {
          const newPublications = new Map(state.remotePublications);
          newPublications.delete(cameraId);
          return { remotePublications: newPublications };
        });
      }
    }
  },
  
  // === SELECTORES ===
  
  getAuthenticatedServers: () => {
    return get().remoteServers.filter(server => {
      const authStatus = get().authStatuses.get(server.id);
      return authStatus?.is_authenticated;
    });
  },
  
  getRemotePublicationByCameraId: (cameraId) => {
    return get().remotePublications.get(cameraId);
  },
  
  isPublishingRemotely: (cameraId) => {
    return mediamtxRemoteService.isPublishingRemotely(cameraId);
  },
  
  getRemotePublicationCounts: () => {
    return mediamtxRemoteService.getRemotePublicationsSummary();
  }
});