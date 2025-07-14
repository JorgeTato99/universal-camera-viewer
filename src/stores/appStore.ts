import { create } from "zustand";
import { AppConfig, NavigationState, Theme } from "../types/common.types";

interface AppState {
  // App Configuration
  config: AppConfig;
  theme: Theme;

  // Navigation
  navigation: NavigationState;

  // UI State
  sidebarOpen: boolean;
  isFullscreen: boolean;

  // Loading & Error States
  isInitializing: boolean;
  globalError: string | null;

  // Actions
  setConfig: (config: Partial<AppConfig>) => void;
  setTheme: (theme: Partial<Theme>) => void;
  navigate: (path: string) => void;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  setFullscreen: (fullscreen: boolean) => void;
  setGlobalError: (error: string | null) => void;
  initialize: () => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Initial State
  config: {
    app_name: "Universal Camera Viewer",
    version: "2.0.0",
    theme_mode: "light",
    language: "es",
    auto_save: true,
    notifications_enabled: true,
  },

  theme: {
    mode: "light",
    primaryColor: "#1976d2",
    secondaryColor: "#dc004e",
    backgroundColor: "#fafafa",
    surfaceColor: "#ffffff",
    textColor: "#000000",
  },

  navigation: {
    currentPath: "/cameras",
    previousPath: undefined,
    breadcrumbs: ["Inicio", "Cámaras"],
  },

  sidebarOpen: true,
  isFullscreen: false,
  isInitializing: true,
  globalError: null,

  // Actions
  setConfig: (configUpdates) =>
    set((state) => ({
      config: { ...state.config, ...configUpdates },
    })),

  setTheme: (themeUpdates) =>
    set((state) => ({
      theme: { ...state.theme, ...themeUpdates },
    })),

  navigate: (path) =>
    set((state) => ({
      navigation: {
        currentPath: path,
        previousPath: state.navigation.currentPath,
        breadcrumbs: [], // TODO: Generate breadcrumbs based on path
      },
    })),

  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

  setFullscreen: (fullscreen) => set({ isFullscreen: fullscreen }),

  setGlobalError: (error) => set({ globalError: error }),

  initialize: async () => {
    try {
      set({ isInitializing: true });

      // Load saved preferences
      const savedConfig = localStorage.getItem("appConfig");
      if (savedConfig) {
        const config = JSON.parse(savedConfig);
        get().setConfig(config);
      }

      const savedTheme = localStorage.getItem("appTheme");
      if (savedTheme) {
        const theme = JSON.parse(savedTheme);
        get().setTheme(theme);
      }

      // Initialize other services
      await new Promise((resolve) => setTimeout(resolve, 1000)); // Simulate initialization

      set({ isInitializing: false });
    } catch (error) {
      console.error("Error initializing app:", error);
      set({
        isInitializing: false,
        globalError: "Error al inicializar la aplicación",
      });
    }
  },
}));
