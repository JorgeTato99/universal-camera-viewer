/**
 * 🎨 Color System - Universal Camera Viewer
 * Paleta de colores y funciones utilitarias
 */

import { colorTokens } from "./tokens";

// === COLORES SEMÁNTICOS ===
export const colors = {
  // Colores de estado para cámaras
  camera: {
    connected: colorTokens.status.connected,
    connecting: colorTokens.status.connecting,
    disconnected: colorTokens.status.disconnected,
    streaming: colorTokens.status.streaming,
    error: colorTokens.status.error,
    unavailable: colorTokens.status.unavailable,
  },

  // Colores para UI
  ui: {
    primary: colorTokens.primary[500],
    secondary: colorTokens.secondary[500],
    success: colorTokens.alert.success,
    warning: colorTokens.alert.warning,
    error: colorTokens.alert.error,
    info: colorTokens.alert.info,
  },

  // Colores de fondo
  background: {
    default: colorTokens.background.light,
    paper: colorTokens.background.paper,
    surface: colorTokens.background.surface,
    // Modo oscuro
    dark: {
      default: colorTokens.background.dark,
      paper: colorTokens.background.darkPaper,
      surface: colorTokens.background.darkSurface,
    },
  },

  // Colores de texto
  text: {
    primary: colorTokens.neutral[900],
    secondary: colorTokens.neutral[600],
    disabled: colorTokens.neutral[400],
    hint: colorTokens.neutral[500],
    // Modo oscuro
    dark: {
      primary: colorTokens.neutral[50],
      secondary: colorTokens.neutral[300],
      disabled: colorTokens.neutral[600],
      hint: colorTokens.neutral[500],
    },
  },

  // Colores de borde
  border: {
    default: colorTokens.neutral[300],
    focused: colorTokens.primary[500],
    error: colorTokens.alert.error,
    // Modo oscuro
    dark: {
      default: colorTokens.neutral[700],
      focused: colorTokens.primary[400],
      error: colorTokens.alert.error,
    },
  },
};

// === FUNCIONES UTILITARIAS ===

/**
 * Convierte un color hexadecimal a rgba
 */
export function hexToRgba(hex: string, alpha: number = 1): string {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return hex;

  const r = parseInt(result[1], 16);
  const g = parseInt(result[2], 16);
  const b = parseInt(result[3], 16);

  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/**
 * Obtiene el color de estado de una cámara
 */
export function getCameraStatusColor(status: string): string {
  const statusMap: Record<string, string> = {
    connected: colors.camera.connected,
    connecting: colors.camera.connecting,
    disconnected: colors.camera.disconnected,
    streaming: colors.camera.streaming,
    error: colors.camera.error,
    unavailable: colors.camera.unavailable,
  };

  return statusMap[status] || colors.camera.unavailable;
}

/**
 * Genera una paleta de colores para gráficos
 */
export function getChartColors(count: number): string[] {
  const baseColors = [
    colorTokens.primary[500],
    colorTokens.secondary[500],
    colorTokens.alert.info,
    colorTokens.alert.warning,
    colorTokens.alert.error,
    colorTokens.primary[300],
    colorTokens.secondary[300],
    colorTokens.neutral[500],
  ];

  const colors: string[] = [];
  for (let i = 0; i < count; i++) {
    colors.push(baseColors[i % baseColors.length]);
  }

  return colors;
}

/**
 * Aplica opacidad a un color
 */
export function withOpacity(color: string, opacity: number): string {
  if (color.startsWith("#")) {
    return hexToRgba(color, opacity);
  }

  // Si ya es rgba, modificar la opacidad
  if (color.startsWith("rgba")) {
    return color.replace(/[\d.]+\)$/g, `${opacity})`);
  }

  return color;
}

// === CONSTANTES DE COLORES ===
export const BRAND_COLORS = {
  primary: colorTokens.primary[500],
  secondary: colorTokens.secondary[500],
  accent: colorTokens.primary[700],
} as const;

export const STATUS_COLORS = {
  success: colorTokens.alert.success,
  warning: colorTokens.alert.warning,
  error: colorTokens.alert.error,
  info: colorTokens.alert.info,
} as const;

export const CAMERA_STATUS_COLORS = {
  connected: colorTokens.status.connected,
  connecting: colorTokens.status.connecting,
  disconnected: colorTokens.status.disconnected,
  streaming: colorTokens.status.streaming,
  error: colorTokens.status.error,
  unavailable: colorTokens.status.unavailable,
} as const;
