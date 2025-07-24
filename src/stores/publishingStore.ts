/**
 * 🎯 Publishing Store - Universal Camera Viewer
 * Estado global para gestión de publicaciones MediaMTX
 */

import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import {
  PublishConfiguration,
  PublishStatus,
  PublishingHealth,
  PublishMetrics,
  PublishingAlert,
  MediaMTXPath,
  PublishingStatus,
} from "../features/publishing/types";
import { publishingService } from "../services/publishing";
import { notificationStore } from "./notificationStore";
import { mapBackendToFrontendPublishingStatus } from "../utils/statusLabels";
import { apiClient } from "../services/api/apiClient";
import { 
  mediamtxRemoteService,
  MediaMTXServer,
  AuthStatus,
  RemotePublishStatus
} from "../services/publishing/mediamtxRemoteService";

interface PublishingState {
  // === ESTADO PRINCIPAL ===

  // Publicaciones locales activas
  activePublications: Map<string, PublishStatus>;
  
  // === ESTADO REMOTO (NUEVO) ===
  remote: {
    // Servidores MediaMTX remotos
    servers: MediaMTXServer[];
    // Estados de autenticación por servidor
    authStatuses: Map<number, AuthStatus>;
    // Publicaciones remotas activas
    publications: Map<string, RemotePublishStatus>;
    // Servidor seleccionado actualmente
    selectedServerId: number | null;
    // Estado de carga
    isLoadingServers: boolean;
    isLoadingAuth: Map<number, boolean>;
  };

  // Configuraciones de servidores
  configurations: PublishConfiguration[];
  activeConfig: PublishConfiguration | null;

  // Métricas en tiempo real (historial por cámara)
  currentMetrics: Map<string, PublishMetrics[]>;

  // Salud del sistema
  systemHealth: PublishingHealth | null;

  // Alertas activas
  alerts: PublishingAlert[];

  // Paths configurados
  mediamtxPaths: MediaMTXPath[];
  
  // === MÉTRICAS UNIFICADAS ===
  unifiedMetrics: {
    totalViewers: number;
    totalPublications: number;
    localPublications: number;
    remotePublications: number;
    totalBandwidthMbps: number;
  };

  // === ESTADO DE UI ===

  // Estados de carga
  isLoading: boolean;
  isLoadingMetrics: Map<string, boolean>;
  isPublishing: Map<string, boolean>; // Estados de transición

  // Errores
  error: string | null;

  // Configuración de polling
  pollingInterval: number; // en segundos
  pollingEnabled: boolean;

  // === ACCIONES DE CONTROL ===

  // Control de publicaciones locales
  startPublishing: (cameraId: string, forceRestart?: boolean) => Promise<void>;
  stopPublishing: (cameraId: string) => Promise<void>;
  
  // === ACCIONES REMOTAS (NUEVO) ===
  
  // Control de servidores remotos
  fetchRemoteServers: () => Promise<void>;
  authenticateServer: (serverId: number, username: string, password: string) => Promise<boolean>;
  logoutServer: (serverId: number) => Promise<void>;
  selectServer: (serverId: number | null) => void;
  
  // Control de publicaciones remotas
  startRemotePublishing: (cameraId: string, serverId: number) => Promise<void>;
  stopRemotePublishing: (cameraId: string) => Promise<void>;
  fetchRemotePublications: () => Promise<void>;

  // === ACCIONES DE DATOS ===

  // Obtener datos locales
  fetchPublishingStatus: () => Promise<void>;
  fetchMetrics: (cameraId: string) => Promise<void>;
  fetchConfigurations: () => Promise<void>;
  fetchSystemHealth: () => Promise<void>;
  fetchAlerts: () => Promise<void>;
  fetchPaths: (serverId?: number) => Promise<void>;
  
  // === ACCIONES UNIFICADAS (NUEVO) ===
  fetchUnifiedPublications: () => Promise<void>;
  updateUnifiedMetrics: () => void;

  // === ACCIONES DE CONFIGURACIÓN ===

  // Gestión de configuraciones
  createConfiguration: (config: Partial<PublishConfiguration>) => Promise<void>;
  updateConfiguration: (
    id: number,
    config: Partial<PublishConfiguration>
  ) => Promise<void>;
  deleteConfiguration: (id: number) => Promise<void>;
  activateConfiguration: (name: string) => Promise<void>;

  // Gestión de paths
  createPath: (path: Partial<MediaMTXPath>) => Promise<void>;
  updatePath: (id: number, path: Partial<MediaMTXPath>) => Promise<void>;
  deletePath: (id: number) => Promise<void>;
  testPath: (id: number) => Promise<boolean>;

  // === UTILIDADES ===

  // Manejo de errores
  clearError: () => void;

  // Polling
  setPollingInterval: (seconds: number) => void;
  setPollingEnabled: (enabled: boolean) => void;

  // Alertas
  dismissAlert: (alertId: string) => void;

  // Métricas
  clearMetrics: (cameraId?: string) => void;
  addMetricSample: (cameraId: string, metric: PublishMetrics) => void;

  // === SELECTORES ===

  // Obtener publicación por cámara
  getPublicationByCameraId: (cameraId: string) => PublishStatus | undefined;

  // Contar publicaciones por estado
  getPublicationCounts: () => {
    total: number;
    running: number;
    error: number;
    starting: number;
    stopping: number;
  };

  // Obtener métricas recientes
  getLatestMetrics: (cameraId: string, count?: number) => PublishMetrics[];

  // Verificar si está publicando
  isPublishingActive: (cameraId: string) => boolean;
  
  // === SELECTORES REMOTOS (NUEVO) ===
  
  // Obtener publicación remota por cámara
  getRemotePublicationByCameraId: (cameraId: string) => RemotePublishStatus | undefined;
  
  // Verificar si está publicando remotamente
  isPublishingRemotely: (cameraId: string) => boolean;
  
  // Obtener servidores autenticados
  getAuthenticatedServers: () => MediaMTXServer[];
  
  // Verificar si un servidor está autenticado
  isServerAuthenticated: (serverId: number) => boolean;
  
  // Obtener publicación unificada (local + remota)
  getUnifiedPublication: (cameraId: string) => {
    local?: PublishStatus;
    remote?: RemotePublishStatus;
    isPublishing: boolean;
    publishingType: 'none' | 'local' | 'remote' | 'both';
  };
}

// Constante para límite de métricas en memoria
const MAX_METRICS_PER_CAMERA = 100;

export const usePublishingStore = create<PublishingState>()(
  subscribeWithSelector((set, get) => ({
    // === ESTADO INICIAL ===

    activePublications: new Map(),
    
    // Estado remoto inicial
    remote: {
      servers: [],
      authStatuses: new Map(),
      publications: new Map(),
      selectedServerId: null,
      isLoadingServers: false,
      isLoadingAuth: new Map(),
    },
    
    configurations: [],
    activeConfig: null,
    currentMetrics: new Map(),
    systemHealth: null,
    alerts: [],
    mediamtxPaths: [],
    
    // Métricas unificadas iniciales
    unifiedMetrics: {
      totalViewers: 0,
      totalPublications: 0,
      localPublications: 0,
      remotePublications: 0,
      totalBandwidthMbps: 0,
    },

    isLoading: false,
    isLoadingMetrics: new Map(),
    isPublishing: new Map(),
    error: null,

    pollingInterval: 5, // 5 segundos por defecto
    pollingEnabled: true,

    // === IMPLEMENTACIÓN DE ACCIONES ===

    // Control de publicaciones
    startPublishing: async (cameraId, forceRestart = false) => {
      // Marcar como iniciando
      set((state) => ({
        isPublishing: new Map(state.isPublishing).set(cameraId, true),
        error: null,
      }));

      try {
        const response = await publishingService.startPublishing({
          camera_id: cameraId,
          force_restart: forceRestart,
        });

        if (response.success && response.data) {
          // Actualizar estado local inmediatamente
          set((state) => ({
            activePublications: new Map(state.activePublications).set(
              cameraId,
              response.data!
            ),
            isPublishing: new Map(state.isPublishing).set(cameraId, false),
          }));

          // Notificar éxito
          notificationStore.showSuccess(
            "Publicación iniciada",
            `Publicación iniciada para cámara ${cameraId}`
          );
        } else {
          throw new Error(response.error || "Error al iniciar publicación");
        }
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Error desconocido";
        set((state) => ({
          error: errorMessage,
          isPublishing: new Map(state.isPublishing).set(cameraId, false),
        }));

        // Notificar error
        notificationStore.showError(
          "Error al iniciar publicación",
          errorMessage
        );

        throw error;
      }
    },

    stopPublishing: async (cameraId) => {
      // Estado STOPPING local para mejor UX
      set((state) => {
        const newPublications = new Map(state.activePublications);
        const publication = newPublications.get(cameraId);
        
        if (publication) {
          // Estado transitorio solo en frontend
          publication.status = PublishingStatus.STOPPING;
        }
        
        return {
          activePublications: newPublications,
          isPublishing: new Map(state.isPublishing).set(cameraId, true),
          error: null,
        };
      });

      try {
        const response = await publishingService.stopPublishing({
          camera_id: cameraId,
        });

        if (response.success) {
          // Actualizar estado local
          set((state) => {
            const newPublications = new Map(state.activePublications);
            const publication = newPublications.get(cameraId);

            if (publication) {
              publication.status = PublishingStatus.IDLE;
              publication.uptime_seconds = 0;
            }

            return {
              activePublications: newPublications,
              isPublishing: new Map(state.isPublishing).set(cameraId, false),
            };
          });

          // Limpiar métricas
          get().clearMetrics(cameraId);

          // Notificar éxito
          notificationStore.showInfo(
            "Publicación detenida",
            `Publicación detenida para cámara ${cameraId}`
          );
        } else {
          throw new Error(response.error || "Error al detener publicación");
        }
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Error desconocido";
        set((state) => ({
          error: errorMessage,
          isPublishing: new Map(state.isPublishing).set(cameraId, false),
        }));

        // Notificar error
        notificationStore.showError(
          "Error al detener publicación",
          errorMessage
        );

        throw error;
      }
    },

    // Obtener estado de publicaciones
    fetchPublishingStatus: async () => {
      set({ isLoading: true, error: null });

      try {
        const response = await publishingService.getAllPublishingStatus();

        if (response.success && response.data) {
          const newPublications = new Map<string, PublishStatus>();
          response.data.forEach((pub) => {
            // Mapear estado del backend al frontend
            const context = {
              isReconnecting: pub.metrics?.is_reconnecting || false,
              isStopping: false // El backend no envía STOPPING
            };
            
            const mappedStatus = mapBackendToFrontendPublishingStatus(
              pub.status,
              context
            );
            
            // Actualizar el estado con el mapeado
            newPublications.set(pub.camera_id, {
              ...pub,
              status: mappedStatus as PublishingStatus
            });
          });

          set({
            activePublications: newPublications,
            isLoading: false,
          });
        } else {
          throw new Error(response.error || "Error al obtener estado");
        }
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Error desconocido";
        set({
          error: errorMessage,
          isLoading: false,
        });
      }
    },

    // Obtener métricas de una cámara
    fetchMetrics: async (cameraId) => {
      // Marcar como cargando métricas
      set((state) => ({
        isLoadingMetrics: new Map(state.isLoadingMetrics).set(cameraId, true),
      }));

      try {
        const response = await publishingService.getMetrics(cameraId);

        if (response.success && response.data) {
          get().addMetricSample(cameraId, response.data);
        }
      } catch (error) {
        console.error(`Error al obtener métricas para ${cameraId}:`, error);
      } finally {
        set((state) => ({
          isLoadingMetrics: new Map(state.isLoadingMetrics).set(
            cameraId,
            false
          ),
        }));
      }
    },

    // Obtener configuraciones
    fetchConfigurations: async () => {
      try {
        const [configsResponse, activeResponse] = await Promise.all([
          publishingService.getConfigurations(),
          publishingService.getActiveConfiguration().catch(() => null),
        ]);

        if (configsResponse.success && configsResponse.data) {
          set({
            configurations: configsResponse.data,
            activeConfig: activeResponse?.data || null,
          });
        }
      } catch (error) {
        console.error("Error al obtener configuraciones:", error);
      }
    },

    // Obtener salud del sistema
    fetchSystemHealth: async () => {
      try {
        const response = await publishingService.getSystemHealth();

        if (response.success && response.data) {
          set({ systemHealth: response.data });

          // Si hay alertas críticas, notificar
          const criticalAlerts = response.data.active_alerts.filter(
            (alert) => alert.severity === "critical"
          );

          if (criticalAlerts.length > 0) {
            notificationStore.showError(
              "Alertas críticas",
              `${criticalAlerts.length} alerta(s) crítica(s) en el sistema`
            );
          }
        }
      } catch (error) {
        console.error("Error al obtener salud del sistema:", error);
      }
    },

    // Obtener alertas
    fetchAlerts: async () => {
      try {
        const response = await publishingService.getAlerts();

        if (response.success && response.data) {
          set({
            alerts: response.data.map((alert) => ({
              ...alert,
              severity: alert.severity as "info" | "warning" | "error" | "critical",
              alert_type: (alert as any).alert_type || "general",
              dismissible: alert.dismissible ?? true,
            })),
          });
        }
      } catch (error) {
        console.error("Error al obtener alertas:", error);
      }
    },

    // Obtener paths
    fetchPaths: async (serverId) => {
      try {
        const response = await publishingService.getPaths(serverId, true);

        if (response.success && response.data) {
          set({ mediamtxPaths: response.data });
        }
      } catch (error) {
        console.error("Error al obtener paths:", error);
      }
    },

    // Crear configuración
    createConfiguration: async (config) => {
      set({ error: null });

      try {
        const response = await publishingService.createConfiguration(
          config as any
        );

        if (response.success && response.data) {
          set((state) => ({
            configurations: [...state.configurations, response.data!],
          }));

          notificationStore.showSuccess(
            "Configuración creada",
            "Configuración creada exitosamente"
          );
        } else {
          throw new Error(response.error || "Error al crear configuración");
        }
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Error desconocido";
        set({ error: errorMessage });
        throw error;
      }
    },

    // Actualizar configuración
    updateConfiguration: async (id, config) => {
      set({ error: null });

      try {
        const configToUpdate = get().configurations.find((c) => c.id === id);
        if (!configToUpdate) throw new Error("Configuración no encontrada");

        const response = await publishingService.updateConfiguration(
          configToUpdate.name,
          config
        );

        if (response.success && response.data) {
          set((state) => ({
            configurations: state.configurations.map((c) =>
              c.id === id ? response.data! : c
            ),
            activeConfig:
              state.activeConfig?.id === id
                ? response.data!
                : state.activeConfig,
          }));

          notificationStore.showSuccess(
            "Configuración actualizada",
            "Configuración actualizada exitosamente"
          );
        } else {
          throw new Error(
            response.error || "Error al actualizar configuración"
          );
        }
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Error desconocido";
        set({ error: errorMessage });
        throw error;
      }
    },

    // Eliminar configuración
    deleteConfiguration: async (id) => {
      set({ error: null });

      try {
        const configToDelete = get().configurations.find((c) => c.id === id);
        if (!configToDelete) throw new Error("Configuración no encontrada");

        const response = await publishingService.deleteConfiguration(
          configToDelete.name
        );

        if (response.success) {
          set((state) => ({
            configurations: state.configurations.filter((c) => c.id !== id),
            activeConfig:
              state.activeConfig?.id === id ? null : state.activeConfig,
          }));

          notificationStore.showInfo(
            "Configuración eliminada",
            "Configuración eliminada exitosamente"
          );
        } else {
          throw new Error(response.error || "Error al eliminar configuración");
        }
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Error desconocido";
        set({ error: errorMessage });
        throw error;
      }
    },

    // Activar configuración
    activateConfiguration: async (name) => {
      set({ error: null });

      try {
        const response = await publishingService.activateConfiguration(name);

        if (response.success && response.data) {
          set((state) => ({
            activeConfig: response.data!,
            configurations: state.configurations.map((c) => ({
              ...c,
              is_active: c.name === name,
            })),
          }));

          notificationStore.showSuccess(
            "Configuración activada",
            `Configuración "${name}" activada`
          );
        } else {
          throw new Error(response.error || "Error al activar configuración");
        }
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Error desconocido";
        set({ error: errorMessage });
        throw error;
      }
    },

    // Crear path
    createPath: async (path) => {
      try {
        const response = await publishingService.createPath(path as any);

        if (response.success && response.data) {
          set((state) => ({
            mediamtxPaths: [...state.mediamtxPaths, response.data!],
          }));

          notificationStore.showSuccess(
            "Path creado",
            "Path creado exitosamente"
          );
        } else {
          throw new Error(response.error || "Error al crear path");
        }
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Error desconocido";
        throw new Error(errorMessage);
      }
    },

    // Actualizar path
    updatePath: async (id, path) => {
      try {
        const response = await publishingService.updatePath(id, path);

        if (response.success && response.data) {
          set((state) => ({
            mediamtxPaths: state.mediamtxPaths.map((p) =>
              p.id === id ? response.data! : p
            ),
          }));

          notificationStore.showSuccess(
            "Path actualizado",
            "Path actualizado exitosamente"
          );
        } else {
          throw new Error(response.error || "Error al actualizar path");
        }
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Error desconocido";
        throw new Error(errorMessage);
      }
    },

    // Eliminar path
    deletePath: async (id) => {
      try {
        const response = await publishingService.deletePath(id);

        if (response.success) {
          set((state) => ({
            mediamtxPaths: state.mediamtxPaths.filter((p) => p.id !== id),
          }));

          notificationStore.showInfo(
            "Path eliminado",
            "Path eliminado exitosamente"
          );
        } else {
          throw new Error(response.error || "Error al eliminar path");
        }
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Error desconocido";
        throw new Error(errorMessage);
      }
    },

    // Probar path
    testPath: async (id) => {
      try {
        const response = await publishingService.testPath(id);

        if (response.success && response.data) {
          const { success, message } = response.data;

          if (success) {
            notificationStore.showSuccess("Conexión exitosa", "La conexión se estableció correctamente");
          } else {
            notificationStore.showError("Fallo en conexión", message);
          }

          return success;
        }

        return false;
      } catch (error) {
        notificationStore.showError(
          "Error de conexión",
          "Error al probar conexión"
        );
        return false;
      }
    },

    // === ACCIONES REMOTAS ===
    
    // Cargar servidores remotos
    fetchRemoteServers: async () => {
      set((state) => ({
        remote: {
          ...state.remote,
          isLoadingServers: true,
        },
      }));

      try {
        // Cargar servidores desde el endpoint real
        const response = await apiClient.get<MediaMTXServer[]>('/mediamtx/servers');
        
        if (response.success && response.data) {
          set((state) => ({
            remote: {
              ...state.remote,
              servers: response.data!,
              isLoadingServers: false,
            },
          }));
          
          // Cargar estados de autenticación para cada servidor
          const authPromises = response.data.map(server => 
            mediamtxRemoteService.getAuthStatus(server.id)
          );
          
          const authResponses = await Promise.allSettled(authPromises);
          
          // Actualizar estados de autenticación
          const authStatuses = new Map<number, AuthStatus>();
          authResponses.forEach((result, index) => {
            if (result.status === 'fulfilled' && result.value.success && result.value.data) {
              const serverId = response.data![index].id;
              authStatuses.set(serverId, result.value.data as AuthStatus);
            }
          });
          
          set((state) => ({
            remote: {
              ...state.remote,
              authStatuses,
            },
          }));
        } else {
          throw new Error('Error cargando servidores');
        }
        
      } catch (error) {
        console.error('Error cargando servidores:', error);
        set((state) => ({
          remote: {
            ...state.remote,
            isLoadingServers: false,
          },
          error: 'Error cargando servidores remotos',
        }));
      }
    },
    
    // Autenticar servidor
    authenticateServer: async (serverId, username, password) => {
      set((state) => ({
        remote: {
          ...state.remote,
          isLoadingAuth: new Map(state.remote.isLoadingAuth).set(serverId, true),
        },
      }));
      
      try {
        const response = await mediamtxRemoteService.authenticate({
          server_id: serverId,
          username,
          password,
        });
        
        if (response.success && response.data) {
          set((state) => ({
            remote: {
              ...state.remote,
              authStatuses: new Map(state.remote.authStatuses).set(serverId, response.data!),
              servers: state.remote.servers.map(server =>
                server.id === serverId
                  ? { ...server, is_authenticated: true }
                  : server
              ),
              isLoadingAuth: new Map(state.remote.isLoadingAuth).set(serverId, false),
            },
          }));
          
          return true;
        }
        
        return false;
      } catch (error) {
        console.error('Error autenticando servidor:', error);
        set((state) => ({
          remote: {
            ...state.remote,
            isLoadingAuth: new Map(state.remote.isLoadingAuth).set(serverId, false),
          },
          error: 'Error autenticando con el servidor',
        }));
        return false;
      }
    },
    
    // Cerrar sesión del servidor
    logoutServer: async (serverId) => {
      try {
        await mediamtxRemoteService.logout(serverId);
        
        set((state) => {
          const newAuthStatuses = new Map(state.remote.authStatuses);
          newAuthStatuses.delete(serverId);
          
          return {
            remote: {
              ...state.remote,
              authStatuses: newAuthStatuses,
              servers: state.remote.servers.map(server =>
                server.id === serverId
                  ? { ...server, is_authenticated: false }
                  : server
              ),
            },
          };
        });
        
        notificationStore.showInfo(
          'Sesión cerrada',
          'Se cerró la sesión del servidor remoto'
        );
      } catch (error) {
        console.error('Error cerrando sesión:', error);
        notificationStore.showError(
          'Error al cerrar sesión',
          'No se pudo cerrar la sesión del servidor'
        );
      }
    },
    
    // Seleccionar servidor
    selectServer: (serverId) => {
      set((state) => ({
        remote: {
          ...state.remote,
          selectedServerId: serverId,
        },
      }));
    },
    
    // Iniciar publicación remota
    startRemotePublishing: async (cameraId, serverId) => {
      set((state) => ({
        isPublishing: new Map(state.isPublishing).set(cameraId, true),
        error: null,
      }));
      
      try {
        const response = await mediamtxRemoteService.startRemotePublishing({
          camera_id: cameraId,
          server_id: serverId,
        });
        
        if (response.success && response.data) {
          set((state) => ({
            remote: {
              ...state.remote,
              publications: new Map(state.remote.publications).set(cameraId, response.data!),
            },
            isPublishing: new Map(state.isPublishing).set(cameraId, false),
          }));
          
          // Actualizar métricas unificadas
          get().updateUnifiedMetrics();
        } else {
          throw new Error(response.error || 'Error al iniciar publicación remota');
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Error desconocido';
        set((state) => ({
          error: errorMessage,
          isPublishing: new Map(state.isPublishing).set(cameraId, false),
        }));
        throw error;
      }
    },
    
    // Detener publicación remota
    stopRemotePublishing: async (cameraId) => {
      set((state) => ({
        isPublishing: new Map(state.isPublishing).set(cameraId, true),
        error: null,
      }));
      
      try {
        const response = await mediamtxRemoteService.stopRemotePublishing(cameraId);
        
        if (response.success) {
          set((state) => {
            const newPublications = new Map(state.remote.publications);
            newPublications.delete(cameraId);
            
            return {
              remote: {
                ...state.remote,
                publications: newPublications,
              },
              isPublishing: new Map(state.isPublishing).set(cameraId, false),
            };
          });
          
          // Actualizar métricas unificadas
          get().updateUnifiedMetrics();
        } else {
          throw new Error(response.error || 'Error al detener publicación remota');
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Error desconocido';
        set((state) => ({
          error: errorMessage,
          isPublishing: new Map(state.isPublishing).set(cameraId, false),
        }));
        throw error;
      }
    },
    
    // Cargar publicaciones remotas
    fetchRemotePublications: async () => {
      try {
        const response = await mediamtxRemoteService.listRemotePublications();
        
        if (response.success && response.data) {
          const newPublications = new Map<string, RemotePublishStatus>();
          response.data.forEach(pub => {
            newPublications.set(pub.camera_id, pub);
          });
          
          set((state) => ({
            remote: {
              ...state.remote,
              publications: newPublications,
            },
          }));
          
          // Actualizar métricas unificadas
          get().updateUnifiedMetrics();
        }
      } catch (error) {
        console.error('Error cargando publicaciones remotas:', error);
      }
    },
    
    // === ACCIONES UNIFICADAS ===
    
    // Cargar publicaciones unificadas
    fetchUnifiedPublications: async () => {
      set({ isLoading: true, error: null });
      
      try {
        // Usar el endpoint unificado
        const response = await apiClient.get<{
          local_publications: PublishStatus[];
          remote_publications: RemotePublishStatus[];
          metrics: {
            total_viewers: number;
            total_publications: number;
            local_publications: number;
            remote_publications: number;
            total_bandwidth_mbps: number;
          };
        }>('/publishing/all');
        
        if (response.success && response.data) {
          // Actualizar publicaciones locales
          const localPubs = new Map<string, PublishStatus>();
          response.data.local_publications.forEach(pub => {
            localPubs.set(pub.camera_id, pub);
          });
          
          // Actualizar publicaciones remotas
          const remotePubs = new Map<string, RemotePublishStatus>();
          response.data.remote_publications.forEach(pub => {
            remotePubs.set(pub.camera_id, pub);
          });
          
          set((state) => ({
            activePublications: localPubs,
            remote: {
              ...state.remote,
              publications: remotePubs,
            },
            unifiedMetrics: response.data.metrics,
            isLoading: false,
          }));
        } else {
          throw new Error('Error cargando publicaciones unificadas');
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Error desconocido';
        set({
          error: errorMessage,
          isLoading: false,
        });
      }
    },
    
    // Actualizar estado de publicación desde WebSocket
    updatePublicationStatus: (cameraId: string, status: any) => {
      const publication: PublishStatus = {
        camera_id: cameraId,
        is_active: status.is_active,
        status: status.status,
        error_message: status.last_error,
        publish_path: '',
        process_id: status.process_id,
        start_time: status.start_time,
        viewers: 0,
        metrics: status.metrics || {
          fps: 0,
          bitrate_kbps: 0,
          resolution: '',
          dropped_frames: 0,
          cpu_percent: 0,
          memory_mb: 0,
        }
      };
      
      set((state) => ({
        activePublications: new Map(state.activePublications).set(cameraId, publication)
      }));
      
      // Actualizar métricas después de actualizar el estado
      get().updateUnifiedMetrics();
    },
    
    // Actualizar métricas unificadas
    updateUnifiedMetrics: () => {
      const state = get();
      const localPubs = Array.from(state.activePublications.values());
      const remotePubs = Array.from(state.remote.publications.values());
      
      let totalViewers = 0;
      let totalBandwidth = 0;
      
      // Sumar métricas locales
      localPubs.forEach(pub => {
        if (pub.metrics) {
          totalViewers += pub.metrics.viewers || 0;
          totalBandwidth += (pub.metrics.bitrate_kbps || 0) / 1000; // Convertir a Mbps
        }
      });
      
      // Sumar métricas remotas
      remotePubs.forEach(pub => {
        if (pub.metrics) {
          totalViewers += pub.metrics.viewers || 0;
          totalBandwidth += (pub.metrics.bitrate_kbps || 0) / 1000;
        }
      });
      
      set({
        unifiedMetrics: {
          totalViewers,
          totalPublications: localPubs.length + remotePubs.length,
          localPublications: localPubs.length,
          remotePublications: remotePubs.length,
          totalBandwidthMbps: Math.round(totalBandwidth * 10) / 10,
        },
      });
    },

    // === UTILIDADES ===

    clearError: () => set({ error: null }),

    setPollingInterval: (seconds) => set({ pollingInterval: seconds }),

    setPollingEnabled: (enabled) => set({ pollingEnabled: enabled }),

    dismissAlert: (alertId) => {
      set((state) => ({
        alerts: state.alerts.filter((alert) => alert.id !== alertId),
      }));

      // También enviar al backend
      publishingService.dismissAlert(alertId).catch(console.error);
    },

    clearMetrics: (cameraId) => {
      set((state) => {
        const newMetrics = new Map(state.currentMetrics);

        if (cameraId) {
          newMetrics.delete(cameraId);
        } else {
          newMetrics.clear();
        }

        return { currentMetrics: newMetrics };
      });
    },

    addMetricSample: (cameraId, metric) => {
      set((state) => {
        const newMetrics = new Map(state.currentMetrics);
        const cameraMetrics = newMetrics.get(cameraId) || [];

        // Agregar nueva métrica al final
        const updatedMetrics = [...cameraMetrics, metric];

        // Mantener solo las últimas N métricas
        if (updatedMetrics.length > MAX_METRICS_PER_CAMERA) {
          updatedMetrics.splice(
            0,
            updatedMetrics.length - MAX_METRICS_PER_CAMERA
          );
        }

        newMetrics.set(cameraId, updatedMetrics);

        return { currentMetrics: newMetrics };
      });
    },

    // === SELECTORES ===

    getPublicationByCameraId: (cameraId) => {
      return get().activePublications.get(cameraId);
    },

    getPublicationCounts: () => {
      const publications = Array.from(get().activePublications.values());

      return {
        total: publications.length,
        running: publications.filter(
          (p) => p.status === PublishingStatus.PUBLISHING
        ).length,
        error: publications.filter((p) => p.status === PublishingStatus.ERROR)
          .length,
        starting: publications.filter(
          (p) => p.status === PublishingStatus.STARTING
        ).length,
        stopping: publications.filter(
          (p) => p.status === PublishingStatus.STOPPING
        ).length,
      };
    },

    getLatestMetrics: (cameraId, count = 10) => {
      const metrics = get().currentMetrics.get(cameraId) || [];
      return metrics.slice(-count);
    },

    isPublishingActive: (cameraId) => {
      const publication = get().activePublications.get(cameraId);
      return publication
        ? publication.status === PublishingStatus.PUBLISHING ||
            publication.status === PublishingStatus.STARTING
        : false;
    },
    
    // === SELECTORES REMOTOS ===
    
    // Obtener publicación remota por cámara
    getRemotePublicationByCameraId: (cameraId) => {
      return get().remote.publications.get(cameraId);
    },
    
    // Verificar si está publicando remotamente
    isPublishingRemotely: (cameraId) => {
      const publication = get().remote.publications.get(cameraId);
      return publication
        ? publication.status === PublishingStatus.PUBLISHING ||
            publication.status === PublishingStatus.STARTING
        : false;
    },
    
    // Obtener servidores autenticados
    getAuthenticatedServers: () => {
      const state = get();
      return state.remote.servers.filter(server => {
        const authStatus = state.remote.authStatuses.get(server.id);
        return authStatus?.is_authenticated || false;
      });
    },
    
    // Verificar si un servidor está autenticado
    isServerAuthenticated: (serverId) => {
      const authStatus = get().remote.authStatuses.get(serverId);
      return authStatus?.is_authenticated || false;
    },
    
    // Obtener publicación unificada (local + remota)
    getUnifiedPublication: (cameraId) => {
      const state = get();
      const local = state.activePublications.get(cameraId);
      const remote = state.remote.publications.get(cameraId);
      
      const isPublishingLocal = local && (
        local.status === PublishingStatus.PUBLISHING ||
        local.status === PublishingStatus.STARTING
      );
      
      const isPublishingRemote = remote && (
        remote.status === PublishingStatus.PUBLISHING ||
        remote.status === PublishingStatus.STARTING
      );
      
      let publishingType: 'none' | 'local' | 'remote' | 'both' = 'none';
      if (isPublishingLocal && isPublishingRemote) {
        publishingType = 'both';
      } else if (isPublishingLocal) {
        publishingType = 'local';
      } else if (isPublishingRemote) {
        publishingType = 'remote';
      }
      
      return {
        local,
        remote,
        isPublishing: isPublishingLocal || isPublishingRemote,
        publishingType,
      };
    },
  }))
);

// Selector helpers para uso en componentes
export const selectActivePublications = (state: PublishingState) =>
  state.activePublications;
export const selectSystemHealth = (state: PublishingState) =>
  state.systemHealth;
export const selectActiveConfig = (state: PublishingState) =>
  state.activeConfig;
export const selectPublicationCounts = (state: PublishingState) =>
  state.getPublicationCounts();

// Nuevos selectors para estado remoto
export const selectRemoteServers = (state: PublishingState) =>
  state.remote.servers;
export const selectRemotePublications = (state: PublishingState) =>
  state.remote.publications;
export const selectAuthStatuses = (state: PublishingState) =>
  state.remote.authStatuses;
export const selectUnifiedMetrics = (state: PublishingState) =>
  state.unifiedMetrics;
export const selectAuthenticatedServers = (state: PublishingState) =>
  state.getAuthenticatedServers();

// Export default
export default usePublishingStore;

// === SISTEMA DE POLLING Y WEBSOCKET ===

// Variables para controlar polling
let pollingInterval: NodeJS.Timeout | null = null;
let wsConnection: WebSocket | null = null;
let wsReconnectTimeout: NodeJS.Timeout | null = null;

/**
 * Iniciar polling de estado
 * Actualiza periódicamente el estado de publicaciones y métricas
 */
export function startPublishingPolling(intervalSeconds: number = 5): void {
  stopPublishingPolling(); // Detener polling existente
  
  const poll = async () => {
    const state = usePublishingStore.getState();
    
    // Solo hacer polling si está habilitado
    if (!state.pollingEnabled) return;
    
    try {
      // Actualizar publicaciones locales
      await state.fetchPublishingStatus();
      
      // Actualizar publicaciones remotas
      await state.fetchRemotePublications();
      
      // Actualizar métricas
      const activePubs = Array.from(state.activePublications.values());
      for (const pub of activePubs) {
        if (pub.status === PublishingStatus.PUBLISHING) {
          await state.fetchMetrics(pub.camera_id);
        }
      }
      
      // Actualizar salud del sistema
      await state.fetchSystemHealth();
      
    } catch (error) {
      console.error('Error en polling de publicaciones:', error);
    }
  };
  
  // Ejecutar inmediatamente
  poll();
  
  // Configurar intervalo
  pollingInterval = setInterval(poll, intervalSeconds * 1000);
}

/**
 * Detener polling de estado
 */
export function stopPublishingPolling(): void {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
  }
}

/**
 * Conectar WebSocket para eventos en tiempo real
 * Complementa el polling con actualizaciones instantáneas
 */
export function connectPublishingWebSocket(wsUrl: string = 'ws://localhost:8000/ws/publishing'): void {
  // Cerrar conexión existente si existe
  disconnectPublishingWebSocket();
  
  try {
    wsConnection = new WebSocket(wsUrl);
    
    wsConnection.onopen = () => {
      console.log('WebSocket de publicaciones conectado');
      
      // Por ahora no enviamos mensaje de suscripción global
      // El handler espera suscripciones a cámaras específicas
      // Las suscripciones se harán cuando se carguen las publicaciones
    };
    
    wsConnection.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (error) {
        console.error('Error procesando mensaje WebSocket:', error);
      }
    };
    
    wsConnection.onerror = (error) => {
      console.error('Error en WebSocket de publicaciones:', error);
    };
    
    wsConnection.onclose = () => {
      console.log('WebSocket de publicaciones desconectado');
      
      // Intentar reconectar después de 5 segundos
      if (!wsReconnectTimeout) {
        wsReconnectTimeout = setTimeout(() => {
          wsReconnectTimeout = null;
          connectPublishingWebSocket(wsUrl);
        }, 5000);
      }
    };
    
  } catch (error) {
    console.error('Error conectando WebSocket:', error);
  }
}

/**
 * Desconectar WebSocket
 */
export function disconnectPublishingWebSocket(): void {
  if (wsReconnectTimeout) {
    clearTimeout(wsReconnectTimeout);
    wsReconnectTimeout = null;
  }
  
  if (wsConnection) {
    wsConnection.close();
    wsConnection = null;
  }
}

/**
 * Suscribirse a eventos de una cámara específica
 */
export function subscribeToCamera(cameraId: string): void {
  if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
    wsConnection.send(JSON.stringify({
      type: 'subscribe_camera',
      camera_id: cameraId
    }));
  }
}

/**
 * Desuscribirse de eventos de una cámara
 */
export function unsubscribeFromCamera(cameraId: string): void {
  if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
    wsConnection.send(JSON.stringify({
      type: 'unsubscribe_camera',
      camera_id: cameraId
    }));
  }
}

/**
 * Iniciar publicación vía WebSocket
 */
export function startPublishingViaWS(cameraId: string, forceRestart: boolean = false): void {
  if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
    wsConnection.send(JSON.stringify({
      type: 'start_publishing',
      camera_id: cameraId,
      force_restart: forceRestart
    }));
  }
}

/**
 * Detener publicación vía WebSocket
 */
export function stopPublishingViaWS(cameraId: string): void {
  if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
    wsConnection.send(JSON.stringify({
      type: 'stop_publishing',
      camera_id: cameraId
    }));
  }
}

/**
 * Obtener estado de una cámara vía WebSocket
 */
export function getStatusViaWS(cameraId: string): void {
  if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
    wsConnection.send(JSON.stringify({
      type: 'get_status',
      camera_id: cameraId
    }));
  }
}

/**
 * Obtener estado de todas las cámaras vía WebSocket
 */
export function getAllStatusViaWS(): void {
  if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
    wsConnection.send(JSON.stringify({
      type: 'get_all_status'
    }));
  }
}

/**
 * Manejar mensajes del WebSocket
 */
function handleWebSocketMessage(data: any): void {
  const state = usePublishingStore.getState();
  
  switch (data.type) {
    case 'connection':
      console.log('WebSocket conectado:', data.message);
      // Solicitar estado inicial de todas las cámaras
      getAllStatusViaWS();
      break;
      
    case 'subscribed':
      console.log(`Suscrito a cámara ${data.camera_id}`);
      if (data.current_status) {
        state.updatePublicationStatus(data.camera_id, data.current_status);
      }
      break;
      
    case 'unsubscribed':
      console.log(`Desuscrito de cámara ${data.camera_id}`);
      break;
      
    case 'publishing_started':
    case 'publishing_failed':
      // Actualizar estado de publicación
      if (data.camera_id) {
        const publication: PublishStatus = {
          camera_id: data.camera_id,
          is_active: data.success,
          status: data.success ? 'running' : 'error',
          error_message: data.error,
          publish_path: data.publish_path,
          process_id: data.process_id,
          start_time: new Date().toISOString(),
          viewers: 0,
          metrics: {
            fps: 0,
            bitrate_kbps: 0,
            resolution: '',
            dropped_frames: 0,
            cpu_percent: 0,
            memory_mb: 0,
          }
        };
        state.activePublications.set(data.camera_id, publication);
        state.updateUnifiedMetrics();
      }
      break;
      
    case 'publishing_stopped':
    case 'stop_failed':
      // Actualizar estado de publicación
      if (data.camera_id && data.success) {
        state.activePublications.delete(data.camera_id);
        state.updateUnifiedMetrics();
      }
      break;
      
    case 'status_response':
      // Actualizar estado individual
      if (data.camera_id && data.status) {
        state.updatePublicationStatus(data.camera_id, data.status);
      }
      break;
      
    case 'all_status_response':
      // Actualizar todos los estados
      if (data.items) {
        const newPublications = new Map<string, PublishStatus>();
        data.items.forEach((item: any) => {
          newPublications.set(item.camera_id, {
            camera_id: item.camera_id,
            is_active: item.is_active,
            status: item.status,
            error_message: item.last_error,
            publish_path: '',
            start_time: item.start_time,
            viewers: 0,
            metrics: item.metrics || {
              fps: 0,
              bitrate_kbps: 0,
              resolution: '',
              dropped_frames: 0,
              cpu_percent: 0,
              memory_mb: 0,
            }
          });
        });
        state.activePublications = newPublications;
        state.updateUnifiedMetrics();
      }
      break;
      
    case 'metrics_update':
      // Actualizar métricas
      if (data.camera_id && data.metrics) {
        const publication = state.activePublications.get(data.camera_id);
        if (publication) {
          publication.metrics = data.metrics;
          state.activePublications.set(data.camera_id, publication);
          state.addMetricSample(data.camera_id, data.metrics);
        }
      }
      break;
      
    case 'error':
      console.error('Error del WebSocket:', data.error);
      break;
      
    case 'publication_status':
      // Actualizar estado de publicación local
      if (data.publication) {
        state.activePublications.set(data.publication.camera_id, data.publication);
        state.updateUnifiedMetrics();
      }
      break;
      
    case 'metrics_update':
      // Actualizar métricas
      if (data.camera_id && data.metrics) {
        state.addMetricSample(data.camera_id, data.metrics);
      }
      break;
      
    case 'remote_publication':
      // Actualizar publicación remota
      if (data.publication) {
        state.remote.publications.set(data.publication.camera_id, data.publication);
        state.updateUnifiedMetrics();
      }
      break;
      
    case 'auth_status':
      // Actualizar estado de autenticación
      if (data.server_id && data.status) {
        state.remote.authStatuses.set(data.server_id, data.status);
      }
      break;
      
    case 'system_health':
      // Actualizar salud del sistema
      if (data.health) {
        usePublishingStore.setState({ systemHealth: data.health });
      }
      break;
      
    case 'alert':
      // Agregar nueva alerta
      if (data.alert) {
        usePublishingStore.setState((prev) => ({
          alerts: [...prev.alerts, data.alert]
        }));
      }
      break;
      
    default:
      console.log('Mensaje WebSocket no manejado:', data.type);
  }
}

// Auto-iniciar polling cuando se carga el módulo
if (typeof window !== 'undefined') {
  // Solo en el navegador
  const state = usePublishingStore.getState();
  if (state.pollingEnabled) {
    startPublishingPolling(state.pollingInterval);
  }
  
  // Conectar WebSocket para actualizaciones en tiempo real
  connectPublishingWebSocket();
}
