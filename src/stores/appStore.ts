import { create } from "zustand";
import { persist, devtools } from "zustand/middleware";
import { AppConfig, NavigationState } from "../types/common.types";

export type ThemeMode = "light" | "dark" | "system";

interface AppState {
  // App Configuration
  config: AppConfig;

  // Theme Management
  themeMode: ThemeMode;
  effectiveTheme: "light" | "dark"; // El tema efectivo después de resolver "system"

  // Navigation
  navigation: NavigationState;

  // UI State
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  isFullscreen: boolean;

  // Loading & Error States
  isInitializing: boolean;
  globalError: string | null;

  // Actions
  setConfig: (config: Partial<AppConfig>) => void;
  setThemeMode: (mode: ThemeMode) => void;
  toggleTheme: () => void;
  setEffectiveTheme: (theme: "light" | "dark") => void;
  navigate: (path: string) => void;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setFullscreen: (fullscreen: boolean) => void;
  setGlobalError: (error: string | null) => void;
  initialize: () => Promise<void>;
}

// Función para detectar preferencia del sistema
const getSystemTheme = (): "light" | "dark" => {
  if (typeof window !== "undefined") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }
  return "light";
};

// Función para resolver el tema efectivo
const resolveEffectiveTheme = (themeMode: ThemeMode): "light" | "dark" => {
  if (themeMode === "system") {
    return getSystemTheme();
  }
  return themeMode;
};

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial State
        config: {
          app_name: "Universal Camera Viewer",
          version: "2.0.0",
          theme_mode: "light",
          language: "es",
          auto_save: true,
          notifications_enabled: true,
        },

        themeMode: "light",
        effectiveTheme: "light",

        navigation: {
          currentPath: "/cameras",
          previousPath: undefined,
          breadcrumbs: ["Inicio", "Cámaras"],
        },

        sidebarOpen: true,
        sidebarCollapsed: false,
        isFullscreen: false,
        isInitializing: true,
        globalError: null,

        // Actions
        setConfig: (configUpdates) =>
          set((state) => ({
            config: { ...state.config, ...configUpdates },
          })),

        setThemeMode: (mode) => {
          const effectiveTheme = resolveEffectiveTheme(mode);
          set({
            themeMode: mode,
            effectiveTheme,
            config: { ...get().config, theme_mode: mode },
          });
        },

        toggleTheme: () => {
          const { themeMode } = get();
          const newMode: ThemeMode = themeMode === "light" ? "dark" : "light";
          const effectiveTheme = resolveEffectiveTheme(newMode);
          set({
            themeMode: newMode,
            effectiveTheme,
            config: { ...get().config, theme_mode: newMode },
          });
        },

        setEffectiveTheme: (theme) => set({ effectiveTheme: theme }),

        navigate: (path) =>
          set((state) => ({
            navigation: {
              currentPath: path,
              previousPath: state.navigation.currentPath,
              breadcrumbs: [], // TODO: Generate breadcrumbs based on path
            },
          })),

        setSidebarOpen: (open) => set({ sidebarOpen: open }),

        toggleSidebar: () =>
          set((state) => ({ sidebarOpen: !state.sidebarOpen })),

        setSidebarCollapsed: (collapsed) =>
          set({ sidebarCollapsed: collapsed }),

        setFullscreen: (fullscreen) => set({ isFullscreen: fullscreen }),

        setGlobalError: (error) => set({ globalError: error }),

        initialize: async () => {
          try {
            set({ isInitializing: true });

            // Resolver tema inicial basado en configuración guardada
            const { themeMode } = get();
            const effectiveTheme = resolveEffectiveTheme(themeMode);

            // Escuchar cambios en la preferencia del sistema
            if (typeof window !== "undefined") {
              const mediaQuery = window.matchMedia(
                "(prefers-color-scheme: dark)"
              );

              const handleSystemThemeChange = (e: MediaQueryListEvent) => {
                const { themeMode } = get();
                if (themeMode === "system") {
                  get().setEffectiveTheme(e.matches ? "dark" : "light");
                }
              };

              mediaQuery.addEventListener("change", handleSystemThemeChange);
            }

            // Initialize other services
            await new Promise((resolve) => setTimeout(resolve, 1000)); // Simulate initialization

            set({
              isInitializing: false,
              effectiveTheme,
            });
          } catch (error) {
            console.error("Error initializing app:", error);
            set({
              isInitializing: false,
              globalError: "Error al inicializar la aplicación",
            });
          }
        },
      }),
      {
        name: "app-store",
        partialize: (state) => ({
          themeMode: state.themeMode,
          sidebarCollapsed: state.sidebarCollapsed,
          sidebarOpen: state.sidebarOpen,
          config: state.config,
        }),
      }
    ),
    { name: "AppStore" }
  )
);
