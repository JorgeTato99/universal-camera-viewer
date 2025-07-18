import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import { 
  CameraResponse,
  ConnectionStatus,
  CameraGridItem,
  ProtocolType,
  isConnected,
  hasCredentials,
  getPrimaryProtocol,
  getVerifiedEndpoint,
} from "../types/camera.types.v2";
import { cameraServiceV2 } from "../services/python/cameraService.v2";
import { streamingService } from "../services/python/streamingService";
import { notificationStore } from "./notificationStore";

interface CameraStateV2 {
  // Camera Data
  cameras: Map<string, CameraResponse>;
  selectedCamera: CameraResponse | null;
  cameraGridItems: Map<string, CameraGridItem>;

  // UI State
  gridColumns: number;
  viewMode: "grid" | "list" | "detail";
  sortBy: "name" | "status" | "lastUpdated" | "location" | "brand";
  sortDirection: "asc" | "desc";
  filterStatus: ConnectionStatus | "all";
  filterBrand: string | "all";
  filterLocation: string | "all";
  searchQuery: string;
  showInactiveCameras: boolean;

  // Loading States
  isLoading: boolean;
  isLoadingCamera: Map<string, boolean>;
  isConnecting: Map<string, boolean>;
  isSaving: Map<string, boolean>;

  // Error States
  errors: Map<string, string>;
  connectionError: {
    hasError: boolean;
    errorType: 'connection' | 'server' | 'timeout' | 'unknown';
    errorMessage: string;
    errorDetails?: string;
  } | null;

  // Actions - Data Management
  loadCameras: () => Promise<void>;
  reloadCamera: (cameraId: string) => Promise<void>;
  addCamera: (camera: CameraResponse) => void;
  createCamera: (cameraData: any) => Promise<void>;
  updateCamera: (cameraId: string, updates: Partial<CameraResponse>) => void;
  removeCamera: (cameraId: string) => void;
  deleteCamera: (cameraId: string) => Promise<void>;
  setSelectedCamera: (camera: CameraResponse | null) => void;

  // Actions - Frame Management
  updateCameraFrame: (cameraId: string, frameData: string) => void;
  updateCameraError: (cameraId: string, error: string | null) => void;
  updateStreamingUrl: (cameraId: string, url: string | null) => void;

  // Actions - Connection Management
  connectCamera: (cameraId: string) => Promise<void>;
  disconnectCamera: (cameraId: string) => Promise<void>;
  updateCredentials: (cameraId: string, username: string, password: string) => Promise<void>;
  saveDiscoveredEndpoint: (cameraId: string, type: string, url: string) => Promise<void>;

  // Actions - UI
  setGridColumns: (columns: number) => void;
  setViewMode: (mode: "grid" | "list" | "detail") => void;
  setSorting: (sortBy: string, direction: "asc" | "desc") => void;
  setFilterStatus: (status: ConnectionStatus | "all") => void;
  setFilterBrand: (brand: string | "all") => void;
  setFilterLocation: (location: string | "all") => void;
  setSearchQuery: (query: string) => void;
  toggleShowInactive: () => void;
  
  // Actions - Error Management
  setConnectionError: (error: any) => void;
  clearConnectionError: () => void;

  // Computed Properties
  getFilteredCameras: () => CameraResponse[];
  getConnectedCameras: () => CameraResponse[];
  getCamerasByLocation: (location: string) => CameraResponse[];
  getCamerasByBrand: (brand: string) => CameraResponse[];
  getCameraStats: () => {
    total: number;
    active: number;
    connected: number;
    streaming: number;
    withCredentials: number;
    byBrand: Record<string, number>;
    byLocation: Record<string, number>;
  };
  getUniqueLocations: () => string[];
  getUniqueBrands: () => string[];

  // Bulk Actions
  connectAllCameras: () => Promise<void>;
  disconnectAllCameras: () => Promise<void>;
  connectCamerasByLocation: (location: string) => Promise<void>;
  
  // Persistence
  exportConfiguration: () => object;
  importConfiguration: (config: object) => Promise<void>;
}

export const useCameraStoreV2 = create<CameraStateV2>()(
  subscribeWithSelector((set, get) => ({
    // Initial State
    cameras: new Map(),
    selectedCamera: null,
    cameraGridItems: new Map(),

    // UI State
    gridColumns: 3,
    viewMode: "grid",
    sortBy: "name",
    sortDirection: "asc",
    filterStatus: "all",
    filterBrand: "all",
    filterLocation: "all",
    searchQuery: "",
    showInactiveCameras: true,

    // Loading States
    isLoading: false,
    isLoadingCamera: new Map(),
    isConnecting: new Map(),
    isSaving: new Map(),

    // Error States
    errors: new Map(),
    connectionError: null,

    // Load all cameras from backend
    loadCameras: async () => {
      // Si ya tenemos cámaras y está cargando, evitar carga duplicada
      const state = get();
      if (state.isLoading && state.cameras.size > 0) {
        console.log('[STORE] Camera loading already in progress, skipping...');
        return;
      }
      
      set({ isLoading: true, connectionError: null });
      try {
        const cameras = await cameraServiceV2.listCameras(
          !get().showInactiveCameras
        );
        
        const camerasMap = new Map<string, CameraResponse>();
        const gridItems = new Map<string, CameraGridItem>();
        
        cameras.forEach(camera => {
          // Asegurar que todas las cámaras empiecen desconectadas al cargar
          const cameraWithCorrectState = {
            ...camera,
            is_connected: false,
            is_streaming: false,
            status: ConnectionStatus.DISCONNECTED,
          };
          
          camerasMap.set(camera.camera_id, cameraWithCorrectState);
          gridItems.set(camera.camera_id, {
            camera: cameraWithCorrectState,
            streaming_url: getVerifiedEndpoint(camera, 'rtsp_main')?.url,
          });
        });
        
        console.log(`[STORE] Loaded ${cameras.length} cameras successfully`);
        set({
          cameras: camerasMap,
          cameraGridItems: gridItems,
          isLoading: false,
          connectionError: null, // Limpiar error si la carga fue exitosa
        });
      } catch (error: any) {
        console.error('Error loading cameras:', error);
        
        // Detectar tipo de error
        const errorMessage = error?.message || 'Error desconocido';
        const isConnectionError = errorMessage.includes('Network Error') || 
                                 errorMessage.includes('ERR_CONNECTION_REFUSED');
        
        // Establecer error de conexión si es apropiado
        if (isConnectionError) {
          set({
            isLoading: false,
            connectionError: {
              hasError: true,
              errorType: 'connection',
              errorMessage: 'No se puede conectar con el servidor backend',
              errorDetails: error?.toString(),
            },
          });
        } else {
          // Para otros errores, usar notificación normal
          notificationStore.addNotification({
            type: 'error',
            message: 'Error al cargar las cámaras',
          });
          set({ isLoading: false });
        }
      }
    },

    // Reload single camera
    reloadCamera: async (cameraId: string) => {
      const loadingMap = new Map(get().isLoadingCamera);
      loadingMap.set(cameraId, true);
      set({ isLoadingCamera: loadingMap });

      try {
        const camera = await cameraServiceV2.getCamera(cameraId);
        // Mantener el estado de conexión actual
        const currentCamera = get().cameras.get(cameraId);
        const updatedCamera = {
          ...camera,
          is_connected: currentCamera?.is_connected || false,
          is_streaming: currentCamera?.is_streaming || false,
          status: currentCamera?.status || ConnectionStatus.DISCONNECTED,
        };
        get().updateCamera(cameraId, updatedCamera);
      } catch (error) {
        console.error(`Error reloading camera ${cameraId}:`, error);
      } finally {
        const loadingMap = new Map(get().isLoadingCamera);
        loadingMap.delete(cameraId);
        set({ isLoadingCamera: loadingMap });
      }
    },

    // Add camera
    addCamera: (camera) =>
      set((state) => {
        const newCameras = new Map(state.cameras);
        newCameras.set(camera.camera_id, camera);

        const newGridItems = new Map(state.cameraGridItems);
        newGridItems.set(camera.camera_id, {
          camera,
          streaming_url: getVerifiedEndpoint(camera, 'rtsp_main')?.url,
        });

        return {
          cameras: newCameras,
          cameraGridItems: newGridItems,
        };
      }),

    // Update camera
    updateCamera: (cameraId, updates) =>
      set((state) => {
        const newCameras = new Map(state.cameras);
        const existingCamera = newCameras.get(cameraId);

        if (existingCamera) {
          const updatedCamera = {
            ...existingCamera,
            ...updates,
            updated_at: new Date().toISOString(),
          };
          newCameras.set(cameraId, updatedCamera);
          
          console.log('[STORE] Camera updated:', {
            cameraId,
            oldStatus: existingCamera.status,
            oldConnected: existingCamera.is_connected,
            newStatus: updatedCamera.status,
            newConnected: updatedCamera.is_connected,
          });

          // Update grid item
          const newGridItems = new Map(state.cameraGridItems);
          const existingGridItem = newGridItems.get(cameraId);
          if (existingGridItem) {
            newGridItems.set(cameraId, {
              ...existingGridItem,
              camera: updatedCamera,
              streaming_url: getVerifiedEndpoint(updatedCamera, 'rtsp_main')?.url,
            });
          }

          // Update selected camera if it's the same
          const newSelectedCamera = 
            state.selectedCamera?.camera_id === cameraId 
              ? updatedCamera 
              : state.selectedCamera;

          return {
            cameras: newCameras,
            cameraGridItems: newGridItems,
            selectedCamera: newSelectedCamera,
          };
        }
        return state;
      }),

    // Remove camera
    removeCamera: (cameraId) =>
      set((state) => {
        const newCameras = new Map(state.cameras);
        newCameras.delete(cameraId);

        const newGridItems = new Map(state.cameraGridItems);
        newGridItems.delete(cameraId);

        const newConnecting = new Map(state.isConnecting);
        newConnecting.delete(cameraId);

        const newErrors = new Map(state.errors);
        newErrors.delete(cameraId);

        return {
          cameras: newCameras,
          cameraGridItems: newGridItems,
          isConnecting: newConnecting,
          errors: newErrors,
          selectedCamera:
            state.selectedCamera?.camera_id === cameraId
              ? null
              : state.selectedCamera,
        };
      }),

    setSelectedCamera: (camera) => set({ selectedCamera: camera }),

    // Create new camera
    createCamera: async (cameraData) => {
      try {
        const response = await cameraServiceV2.createCamera(cameraData);
        
        // Add the new camera to the store
        get().addCamera(response);
        
        notificationStore.addNotification({
          type: 'success',
          message: `Camera "${response.display_name}" created successfully`,
        });
      } catch (error) {
        console.error('Error creating camera:', error);
        notificationStore.addNotification({
          type: 'error',
          message: `Failed to create camera: ${error}`,
        });
        throw error;
      }
    },

    // Delete camera from backend
    deleteCamera: async (cameraId) => {
      try {
        // First disconnect if connected
        const camera = get().cameras.get(cameraId);
        if (camera?.is_connected) {
          await get().disconnectCamera(cameraId);
        }
        
        // Delete from backend
        await cameraServiceV2.deleteCamera(cameraId);
        
        // Remove from store
        get().removeCamera(cameraId);
        
        notificationStore.addNotification({
          type: 'success',
          message: 'Camera deleted successfully',
        });
      } catch (error) {
        console.error('Error deleting camera:', error);
        notificationStore.addNotification({
          type: 'error',
          message: `Failed to delete camera: ${error}`,
        });
        throw error;
      }
    },

    // Frame management
    updateCameraFrame: (cameraId, frameData) =>
      set((state) => {
        const newGridItems = new Map(state.cameraGridItems);
        const existingItem = newGridItems.get(cameraId);

        if (existingItem) {
          newGridItems.set(cameraId, {
            ...existingItem,
            last_frame: frameData,
            error_message: undefined,
          });
        }

        return { cameraGridItems: newGridItems };
      }),

    updateCameraError: (cameraId, error) =>
      set((state) => {
        const newGridItems = new Map(state.cameraGridItems);
        const existingItem = newGridItems.get(cameraId);

        if (existingItem) {
          newGridItems.set(cameraId, {
            ...existingItem,
            error_message: error || undefined,
          });
        }

        const newErrors = new Map(state.errors);
        if (error) {
          newErrors.set(cameraId, error);
        } else {
          newErrors.delete(cameraId);
        }

        return { cameraGridItems: newGridItems, errors: newErrors };
      }),

    updateStreamingUrl: (cameraId, url) =>
      set((state) => {
        const newGridItems = new Map(state.cameraGridItems);
        const existingItem = newGridItems.get(cameraId);

        if (existingItem) {
          newGridItems.set(cameraId, {
            ...existingItem,
            streaming_url: url || undefined,
          });
        }

        return { cameraGridItems: newGridItems };
      }),

    // Connection management
    connectCamera: async (cameraId) => {
      console.log('[STORE] Connecting camera:', cameraId);
      
      // Log camera details before connecting
      const camera = get().cameras.get(cameraId);
      if (camera) {
        console.log('[STORE] Camera details:', {
          id: camera.camera_id,
          name: camera.display_name,
          ip: camera.ip_address,
          brand: camera.brand,
          protocols: camera.protocols?.map(p => ({ type: p.type, port: p.port }))
        });
      }
      
      const connectingMap = new Map(get().isConnecting);
      connectingMap.set(cameraId, true);
      set({ isConnecting: connectingMap });

      try {
        console.log('[STORE] Calling API to connect camera:', cameraId);
        const response = await cameraServiceV2.connectCamera(cameraId);
        console.log('[STORE] Connect response:', response);
        
        // Update status to connected
        console.log('[STORE] Updating camera status to CONNECTED');
        get().updateCamera(cameraId, {
          status: ConnectionStatus.CONNECTED,
          is_connected: true,
          is_streaming: true,
        });

        notificationStore.addNotification({
          type: 'success',
          message: 'Camera connected successfully',
        });

        // NO recargar la cámara ya que perdería el estado de conexión
        // await get().reloadCamera(cameraId);
        
        // Start WebSocket streaming after successful connection
        const camera = get().cameras.get(cameraId);
        if (camera) {
          console.log('[STORE] Starting WebSocket streaming for camera:', cameraId);
          try {
            // Connect to WebSocket for this camera
            await streamingService.connect(cameraId);
            console.log('[STORE] WebSocket connected for camera:', cameraId);
            
            // Start streaming with default configuration
            await streamingService.startStream(cameraId, {
              quality: 'medium',
              fps: 15,
              format: 'jpeg'
            });
            console.log('[STORE] Streaming started for camera:', cameraId);
          } catch (wsError) {
            console.error('[STORE] Failed to start streaming:', wsError);
            // Don't fail the whole connection if streaming fails
            notificationStore.addNotification({
              type: 'warning',
              message: 'Camera connected but streaming failed to start',
            });
          }
        }
      } catch (error) {
        console.error(`Error connecting camera ${cameraId}:`, error);
        get().updateCameraError(cameraId, String(error));
        notificationStore.addNotification({
          type: 'error',
          message: `Failed to connect: ${error}`,
        });
      } finally {
        const connectingMap = new Map(get().isConnecting);
        connectingMap.delete(cameraId);
        set({ isConnecting: connectingMap });
      }
    },

    disconnectCamera: async (cameraId) => {
      try {
        // Stop streaming first if WebSocket exists
        try {
          // Verificar si hay conexión activa antes de intentar detenerla
          if (streamingService.isConnected(cameraId)) {
            await streamingService.stopStream(cameraId);
            streamingService.disconnect(cameraId);
            console.log('[STORE] Streaming stopped for camera:', cameraId);
          } else {
            console.log('[STORE] No active WebSocket connection for camera:', cameraId);
          }
        } catch (wsError) {
          console.warn('[STORE] Error stopping streaming (non-critical):', wsError);
          // No es crítico si el streaming ya estaba detenido
        }
        
        // Then disconnect from backend
        await cameraServiceV2.disconnectCamera(cameraId);
        
        // Update camera state
        get().updateCamera(cameraId, {
          status: ConnectionStatus.DISCONNECTED,
          is_connected: false,
          is_streaming: false,
        });

        notificationStore.addNotification({
          type: 'success',
          message: 'Camera disconnected',
        });
      } catch (error) {
        console.error(`Error disconnecting camera ${cameraId}:`, error);
        
        // Aún así actualizar el estado local aunque falle el backend
        get().updateCamera(cameraId, {
          status: ConnectionStatus.DISCONNECTED,
          is_connected: false,
          is_streaming: false,
        });
        
        notificationStore.addNotification({
          type: 'error',
          message: `Failed to disconnect: ${error}`,
        });
      }
    },

    updateCredentials: async (cameraId, username, password) => {
      const savingMap = new Map(get().isSaving);
      savingMap.set(cameraId, true);
      set({ isSaving: savingMap });

      try {
        const updatedCamera = await cameraServiceV2.updateCredentials(
          cameraId,
          username,
          password
        );
        
        get().updateCamera(cameraId, updatedCamera);
        
        notificationStore.addNotification({
          type: 'success',
          message: 'Credentials updated',
        });
      } catch (error) {
        console.error(`Error updating credentials:`, error);
        notificationStore.addNotification({
          type: 'error',
          message: `Failed to update credentials: ${error}`,
        });
      } finally {
        const savingMap = new Map(get().isSaving);
        savingMap.delete(cameraId);
        set({ isSaving: savingMap });
      }
    },

    saveDiscoveredEndpoint: async (cameraId, type, url) => {
      try {
        await cameraServiceV2.addCameraEndpoint(cameraId, {
          type,
          url,
          verified: true,
        });

        // Reload camera to get updated endpoints
        await get().reloadCamera(cameraId);
        
        notificationStore.addNotification({
          type: 'success',
          message: 'Endpoint saved',
        });
      } catch (error) {
        console.error(`Error saving endpoint:`, error);
        notificationStore.addNotification({
          type: 'error',
          message: `Failed to save endpoint: ${error}`,
        });
      }
    },

    // UI Actions
    setGridColumns: (columns) =>
      set({ gridColumns: Math.max(1, Math.min(6, columns)) }),
    setViewMode: (mode) => set({ viewMode: mode }),
    setSorting: (sortBy, direction) =>
      set({ sortBy: sortBy as any, sortDirection: direction }),
    setFilterStatus: (status) => set({ filterStatus: status }),
    setFilterBrand: (brand) => set({ filterBrand: brand }),
    setFilterLocation: (location) => set({ filterLocation: location }),
    setSearchQuery: (query) => set({ searchQuery: query }),
    toggleShowInactive: () => set(state => ({ 
      showInactiveCameras: !state.showInactiveCameras 
    })),

    // Error Management Actions
    setConnectionError: (error: any) => {
      const errorMessage = error?.message || 'Error desconocido';
      const isConnectionError = errorMessage.includes('Network Error') || 
                               errorMessage.includes('ERR_CONNECTION_REFUSED');
      
      if (isConnectionError) {
        set({
          connectionError: {
            hasError: true,
            errorType: 'connection',
            errorMessage: 'No se puede conectar con el servidor backend',
            errorDetails: error?.toString(),
          },
        });
      }
    },

    clearConnectionError: () => {
      set({ connectionError: null });
    },

    // Computed Properties
    getFilteredCameras: () => {
      const { 
        cameras, 
        filterStatus, 
        filterBrand,
        filterLocation,
        searchQuery, 
        sortBy, 
        sortDirection,
        showInactiveCameras 
      } = get();
      
      let filtered = Array.from(cameras.values());

      // Filter inactive if needed
      if (!showInactiveCameras) {
        filtered = filtered.filter(camera => camera.is_active);
      }

      // Apply status filter
      if (filterStatus !== "all") {
        filtered = filtered.filter(camera => camera.status === filterStatus);
      }

      // Apply brand filter
      if (filterBrand !== "all") {
        filtered = filtered.filter(camera => camera.brand === filterBrand);
      }

      // Apply location filter
      if (filterLocation !== "all") {
        filtered = filtered.filter(camera => camera.location === filterLocation);
      }

      // Apply search
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        filtered = filtered.filter(
          camera =>
            camera.display_name.toLowerCase().includes(query) ||
            camera.ip_address.includes(query) ||
            camera.brand.toLowerCase().includes(query) ||
            camera.model.toLowerCase().includes(query) ||
            camera.location?.toLowerCase().includes(query) ||
            camera.description?.toLowerCase().includes(query)
        );
      }

      // Sort
      filtered.sort((a, b) => {
        let compareValue = 0;
        
        switch (sortBy) {
          case "name":
            compareValue = a.display_name.localeCompare(b.display_name);
            break;
          case "status":
            compareValue = a.status.localeCompare(b.status);
            break;
          case "lastUpdated":
            compareValue = new Date(b.updated_at).getTime() - 
                          new Date(a.updated_at).getTime();
            break;
          case "location":
            compareValue = (a.location || "").localeCompare(b.location || "");
            break;
          case "brand":
            compareValue = a.brand.localeCompare(b.brand);
            break;
        }

        return sortDirection === "asc" ? compareValue : -compareValue;
      });

      return filtered;
    },

    getConnectedCameras: () => {
      const { cameras } = get();
      return Array.from(cameras.values()).filter(camera => 
        isConnected(camera)
      );
    },

    getCamerasByLocation: (location) => {
      const { cameras } = get();
      return Array.from(cameras.values()).filter(
        camera => camera.location === location
      );
    },

    getCamerasByBrand: (brand) => {
      const { cameras } = get();
      return Array.from(cameras.values()).filter(
        camera => camera.brand === brand
      );
    },

    getCameraStats: () => {
      const { cameras } = get();
      const cameraList = Array.from(cameras.values());
      
      const byBrand: Record<string, number> = {};
      const byLocation: Record<string, number> = {};
      
      let active = 0;
      let connected = 0;
      let streaming = 0;
      let withCredentials = 0;
      
      cameraList.forEach(camera => {
        if (camera.is_active) active++;
        if (camera.is_connected) connected++;
        if (camera.is_streaming) streaming++;
        if (hasCredentials(camera)) withCredentials++;
        
        // Count by brand
        byBrand[camera.brand] = (byBrand[camera.brand] || 0) + 1;
        
        // Count by location
        if (camera.location) {
          byLocation[camera.location] = (byLocation[camera.location] || 0) + 1;
        }
      });
      
      return {
        total: cameraList.length,
        active,
        connected,
        streaming,
        withCredentials,
        byBrand,
        byLocation,
      };
    },

    getUniqueLocations: () => {
      const { cameras } = get();
      const locations = new Set<string>();
      
      cameras.forEach(camera => {
        if (camera.location) {
          locations.add(camera.location);
        }
      });
      
      return Array.from(locations).sort();
    },

    getUniqueBrands: () => {
      const { cameras } = get();
      const brands = new Set<string>();
      
      cameras.forEach(camera => {
        brands.add(camera.brand);
      });
      
      return Array.from(brands).sort();
    },

    // Bulk Actions
    connectAllCameras: async () => {
      const cameras = get().getFilteredCameras();
      const disconnected = cameras.filter(
        c => c.status === ConnectionStatus.DISCONNECTED
      );
      
      if (disconnected.length === 0) {
        notificationStore.addNotification({
          type: 'info',
          message: 'No disconnected cameras to connect',
        });
        return;
      }
      
      notificationStore.addNotification({
        type: 'info',
        message: `Connecting ${disconnected.length} cameras...`,
      });
      
      // Connect in batches to avoid overwhelming the system
      const batchSize = 5;
      for (let i = 0; i < disconnected.length; i += batchSize) {
        const batch = disconnected.slice(i, i + batchSize);
        await Promise.allSettled(
          batch.map(camera => get().connectCamera(camera.camera_id))
        );
        
        // Small delay between batches
        if (i + batchSize < disconnected.length) {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
    },

    disconnectAllCameras: async () => {
      const connected = get().getConnectedCameras();
      
      if (connected.length === 0) {
        notificationStore.addNotification({
          type: 'info',
          message: 'No connected cameras to disconnect',
        });
        return;
      }
      
      notificationStore.addNotification({
        type: 'info',
        message: `Disconnecting ${connected.length} cameras...`,
      });
      
      await Promise.allSettled(
        connected.map(camera => get().disconnectCamera(camera.camera_id))
      );
    },

    connectCamerasByLocation: async (location) => {
      const cameras = get().getCamerasByLocation(location);
      const disconnected = cameras.filter(
        c => c.status === ConnectionStatus.DISCONNECTED
      );
      
      if (disconnected.length === 0) {
        notificationStore.addNotification({
          type: 'info',
          message: `No disconnected cameras in ${location}`,
        });
        return;
      }
      
      notificationStore.addNotification({
        type: 'info',
        message: `Connecting ${disconnected.length} cameras in ${location}...`,
      });
      
      await Promise.allSettled(
        disconnected.map(camera => get().connectCamera(camera.camera_id))
      );
    },

    // Configuration export/import
    exportConfiguration: () => {
      const { cameras } = get();
      const config = {
        version: '2.0',
        timestamp: new Date().toISOString(),
        cameras: Array.from(cameras.values()).map(camera => ({
          brand: camera.brand,
          model: camera.model,
          display_name: camera.display_name,
          ip_address: camera.ip_address,
          location: camera.location,
          description: camera.description,
          protocols: camera.protocols,
          endpoints: camera.endpoints.filter(e => e.is_verified),
          stream_profiles: camera.stream_profiles,
          capabilities: camera.capabilities,
        })),
      };
      
      return config;
    },

    importConfiguration: async (config: any) => {
      if (config.version !== '2.0') {
        throw new Error('Incompatible configuration version');
      }
      
      // Import logic would go here
      notificationStore.addNotification({
        type: 'info',
        message: 'Configuration import not yet implemented',
      });
    },
  }))
);