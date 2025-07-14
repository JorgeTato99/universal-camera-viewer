import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import { Camera, ConnectionStatus, CameraGridItem } from "../types";

interface CameraState {
  // Camera Data
  cameras: Map<string, Camera>;
  selectedCamera: Camera | null;
  cameraGridItems: Map<string, CameraGridItem>;

  // UI State
  gridColumns: number;
  viewMode: "grid" | "list";
  sortBy: "name" | "status" | "lastUpdated";
  sortDirection: "asc" | "desc";
  filterStatus: ConnectionStatus | "all";
  searchQuery: string;

  // Loading States
  isLoading: boolean;
  isConnecting: Map<string, boolean>;

  // Actions
  addCamera: (camera: Camera) => void;
  updateCamera: (cameraId: string, updates: Partial<Camera>) => void;
  removeCamera: (cameraId: string) => void;
  setSelectedCamera: (camera: Camera | null) => void;
  updateCameraFrame: (cameraId: string, frameData: string) => void;

  // UI Actions
  setGridColumns: (columns: number) => void;
  setViewMode: (mode: "grid" | "list") => void;
  setSorting: (
    sortBy: "name" | "status" | "lastUpdated",
    direction: "asc" | "desc"
  ) => void;
  setFilter: (status: ConnectionStatus | "all") => void;
  setSearchQuery: (query: string) => void;

  // Connection Actions
  setConnecting: (cameraId: string, connecting: boolean) => void;

  // Computed Properties
  getConnectedCameras: () => Camera[];
  getFilteredCameras: () => Camera[];
  getCameraCount: () => { total: number; connected: number; streaming: number };

  // Bulk Actions
  connectAllCameras: () => void;
  disconnectAllCameras: () => void;

  // Persistence
  saveToLocalStorage: () => void;
  loadFromLocalStorage: () => void;
}

export const useCameraStore = create<CameraState>()(
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
    searchQuery: "",

    // Loading States
    isLoading: false,
    isConnecting: new Map(),

    // Camera Management Actions
    addCamera: (camera) =>
      set((state) => {
        const newCameras = new Map(state.cameras);
        newCameras.set(camera.camera_id, camera);

        const newGridItems = new Map(state.cameraGridItems);
        newGridItems.set(camera.camera_id, { camera });

        return {
          cameras: newCameras,
          cameraGridItems: newGridItems,
        };
      }),

    updateCamera: (cameraId, updates) =>
      set((state) => {
        const newCameras = new Map(state.cameras);
        const existingCamera = newCameras.get(cameraId);

        if (existingCamera) {
          const updatedCamera = {
            ...existingCamera,
            ...updates,
            last_updated: new Date().toISOString(),
          };
          newCameras.set(cameraId, updatedCamera);

          // Update grid item
          const newGridItems = new Map(state.cameraGridItems);
          const existingGridItem = newGridItems.get(cameraId);
          if (existingGridItem) {
            newGridItems.set(cameraId, {
              ...existingGridItem,
              camera: updatedCamera,
            });
          }

          return {
            cameras: newCameras,
            cameraGridItems: newGridItems,
          };
        }
        return state;
      }),

    removeCamera: (cameraId) =>
      set((state) => {
        const newCameras = new Map(state.cameras);
        newCameras.delete(cameraId);

        const newGridItems = new Map(state.cameraGridItems);
        newGridItems.delete(cameraId);

        const newConnecting = new Map(state.isConnecting);
        newConnecting.delete(cameraId);

        return {
          cameras: newCameras,
          cameraGridItems: newGridItems,
          isConnecting: newConnecting,
          selectedCamera:
            state.selectedCamera?.camera_id === cameraId
              ? null
              : state.selectedCamera,
        };
      }),

    setSelectedCamera: (camera) => set({ selectedCamera: camera }),

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

    // UI Actions
    setGridColumns: (columns) =>
      set({ gridColumns: Math.max(1, Math.min(6, columns)) }),
    setViewMode: (mode) => set({ viewMode: mode }),
    setSorting: (sortBy, direction) =>
      set({ sortBy, sortDirection: direction }),
    setFilter: (status) => set({ filterStatus: status }),
    setSearchQuery: (query) => set({ searchQuery: query }),

    // Connection Actions
    setConnecting: (cameraId, connecting) =>
      set((state) => {
        const newConnecting = new Map(state.isConnecting);
        if (connecting) {
          newConnecting.set(cameraId, true);
        } else {
          newConnecting.delete(cameraId);
        }
        return { isConnecting: newConnecting };
      }),

    // Computed Properties
    getConnectedCameras: () => {
      const { cameras } = get();
      return Array.from(cameras.values()).filter(
        (camera) => camera.is_connected
      );
    },

    getFilteredCameras: () => {
      const { cameras, filterStatus, searchQuery, sortBy, sortDirection } =
        get();
      let filtered = Array.from(cameras.values());

      // Apply status filter
      if (filterStatus !== "all") {
        filtered = filtered.filter((camera) => camera.status === filterStatus);
      }

      // Apply search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        filtered = filtered.filter(
          (camera) =>
            camera.display_name.toLowerCase().includes(query) ||
            camera.connection_config.ip.includes(query) ||
            camera.brand.toLowerCase().includes(query)
        );
      }

      // Apply sorting
      filtered.sort((a, b) => {
        let aValue: any, bValue: any;

        switch (sortBy) {
          case "name":
            aValue = a.display_name.toLowerCase();
            bValue = b.display_name.toLowerCase();
            break;
          case "status":
            aValue = a.status;
            bValue = b.status;
            break;
          case "lastUpdated":
            aValue = new Date(a.last_updated);
            bValue = new Date(b.last_updated);
            break;
          default:
            return 0;
        }

        if (aValue < bValue) return sortDirection === "asc" ? -1 : 1;
        if (aValue > bValue) return sortDirection === "asc" ? 1 : -1;
        return 0;
      });

      return filtered;
    },

    getCameraCount: () => {
      const { cameras } = get();
      const cameraArray = Array.from(cameras.values());

      return {
        total: cameraArray.length,
        connected: cameraArray.filter((c) => c.is_connected).length,
        streaming: cameraArray.filter((c) => c.is_streaming).length,
      };
    },

    // Bulk Actions
    connectAllCameras: () => {
      // This will be handled by the service layer
      console.log("Connect all cameras requested");
    },

    disconnectAllCameras: () => {
      // This will be handled by the service layer
      console.log("Disconnect all cameras requested");
    },

    // Persistence
    saveToLocalStorage: () => {
      const { cameras, gridColumns, viewMode, sortBy, sortDirection } = get();
      const dataToSave = {
        cameras: Array.from(cameras.entries()),
        gridColumns,
        viewMode,
        sortBy,
        sortDirection,
        timestamp: new Date().toISOString(),
      };
      localStorage.setItem("cameraStore", JSON.stringify(dataToSave));
    },

    loadFromLocalStorage: () => {
      try {
        const saved = localStorage.getItem("cameraStore");
        if (saved) {
          const data = JSON.parse(saved);
          set({
            cameras: new Map(data.cameras || []),
            gridColumns: data.gridColumns || 3,
            viewMode: data.viewMode || "grid",
            sortBy: data.sortBy || "name",
            sortDirection: data.sortDirection || "asc",
          });
        }
      } catch (error) {
        console.error("Error loading camera store from localStorage:", error);
      }
    },
  }))
);
