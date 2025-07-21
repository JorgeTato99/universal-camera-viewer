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

interface PublishingState {
  // === ESTADO PRINCIPAL ===

  // Publicaciones activas
  activePublications: Map<string, PublishStatus>;

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

  // Control de publicaciones
  startPublishing: (cameraId: string, forceRestart?: boolean) => Promise<void>;
  stopPublishing: (cameraId: string) => Promise<void>;

  // === ACCIONES DE DATOS ===

  // Obtener datos
  fetchPublishingStatus: () => Promise<void>;
  fetchMetrics: (cameraId: string) => Promise<void>;
  fetchConfigurations: () => Promise<void>;
  fetchSystemHealth: () => Promise<void>;
  fetchAlerts: () => Promise<void>;
  fetchPaths: (serverId?: number) => Promise<void>;

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
}

// Constante para límite de métricas en memoria
const MAX_METRICS_PER_CAMERA = 100;

export const usePublishingStore = create<PublishingState>()(
  subscribeWithSelector((set, get) => ({
    // === ESTADO INICIAL ===

    activePublications: new Map(),
    configurations: [],
    activeConfig: null,
    currentMetrics: new Map(),
    systemHealth: null,
    alerts: [],
    mediamtxPaths: [],

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
      // Marcar como deteniendo
      set((state) => ({
        isPublishing: new Map(state.isPublishing).set(cameraId, true),
        error: null,
      }));

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
            newPublications.set(pub.camera_id, pub);
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
          (p) => p.status === PublishingStatus.RUNNING
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
        ? publication.status === PublishingStatus.RUNNING ||
            publication.status === PublishingStatus.STARTING
        : false;
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

// Export default
export default usePublishingStore;
