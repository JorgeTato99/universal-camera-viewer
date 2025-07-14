/**
 * 🎨 useTheme Hook - Universal Camera Viewer
 * Hook personalizado para manejar temas dark/light mode
 */

import { useMemo } from "react";
import { useAppStore } from "../stores/appStore";
import { getTheme } from "../design-system/theme";
import type { Theme } from "@mui/material/styles";

export interface UseThemeReturn {
  theme: Theme;
  themeMode: "light" | "dark" | "system";
  effectiveTheme: "light" | "dark";
  isDark: boolean;
  isLight: boolean;
  toggleTheme: () => void;
  setThemeMode: (mode: "light" | "dark" | "system") => void;
}

export const useTheme = (): UseThemeReturn => {
  const { themeMode, effectiveTheme, toggleTheme, setThemeMode } =
    useAppStore();

  // Crear el tema Material-UI basado en el tema efectivo
  const theme = useMemo(() => {
    return getTheme(effectiveTheme);
  }, [effectiveTheme]);

  // Propiedades derivadas
  const isDark = effectiveTheme === "dark";
  const isLight = effectiveTheme === "light";

  return {
    theme,
    themeMode,
    effectiveTheme,
    isDark,
    isLight,
    toggleTheme,
    setThemeMode,
  };
};
