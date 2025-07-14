/**
 * 🎨 Breakpoints System - Universal Camera Viewer
 * Sistema de breakpoints para diseño responsivo
 */

import { breakpointTokens } from "./tokens";

// === DEFINICIÓN DE BREAKPOINTS ===
export const breakpoints = {
  xs: breakpointTokens.xs, // 0px - Mobile pequeño
  sm: breakpointTokens.sm, // 600px - Mobile grande
  md: breakpointTokens.md, // 900px - Tablet
  lg: breakpointTokens.lg, // 1200px - Desktop
  xl: breakpointTokens.xl, // 1536px - Desktop grande
} as const;

// === FUNCIONES UTILITARIAS ===

/**
 * Genera media query para un breakpoint
 */
export function mediaQuery(size: keyof typeof breakpoints) {
  return `@media (min-width: ${breakpoints[size]}px)`;
}

/**
 * Genera media query para un rango de breakpoints
 */
export function mediaQueryBetween(
  min: keyof typeof breakpoints,
  max: keyof typeof breakpoints
) {
  return `@media (min-width: ${breakpoints[min]}px) and (max-width: ${
    breakpoints[max] - 1
  }px)`;
}

/**
 * Genera media query para máximo tamaño
 */
export function mediaQueryDown(size: keyof typeof breakpoints) {
  return `@media (max-width: ${breakpoints[size] - 1}px)`;
}

/**
 * Obtiene el número de columnas para el grid de cámaras según el breakpoint
 */
export function getCameraGridColumns(width: number): number {
  if (width >= breakpoints.xl) return 4;
  if (width >= breakpoints.lg) return 3;
  if (width >= breakpoints.md) return 2;
  if (width >= breakpoints.sm) return 2;
  return 1;
}

/**
 * Obtiene el tamaño de sidebar según el breakpoint
 */
export function getSidebarWidth(width: number): string {
  if (width >= breakpoints.md) return "280px";
  return "240px";
}

/**
 * Determina si el sidebar debe estar colapsado
 */
export function shouldCollapseSidebar(width: number): boolean {
  return width < breakpoints.md;
}

// === CONFIGURACIONES RESPONSIVAS ===

/**
 * Configuración del grid de cámaras por breakpoint
 */
export const cameraGridConfig = {
  xs: {
    columns: 1,
    gap: "8px",
    padding: "12px",
  },
  sm: {
    columns: 2,
    gap: "12px",
    padding: "16px",
  },
  md: {
    columns: 2,
    gap: "16px",
    padding: "20px",
  },
  lg: {
    columns: 3,
    gap: "20px",
    padding: "24px",
  },
  xl: {
    columns: 4,
    gap: "24px",
    padding: "32px",
  },
} as const;

/**
 * Configuración de navegación por breakpoint
 */
export const navigationConfig = {
  xs: {
    sidebarWidth: "0px",
    sidebarCollapsed: true,
    topbarHeight: "56px",
    showBurgerMenu: true,
  },
  sm: {
    sidebarWidth: "0px",
    sidebarCollapsed: true,
    topbarHeight: "64px",
    showBurgerMenu: true,
  },
  md: {
    sidebarWidth: "240px",
    sidebarCollapsed: false,
    topbarHeight: "64px",
    showBurgerMenu: false,
  },
  lg: {
    sidebarWidth: "280px",
    sidebarCollapsed: false,
    topbarHeight: "64px",
    showBurgerMenu: false,
  },
  xl: {
    sidebarWidth: "320px",
    sidebarCollapsed: false,
    topbarHeight: "64px",
    showBurgerMenu: false,
  },
} as const;

/**
 * Configuración de modal por breakpoint
 */
export const modalConfig = {
  xs: {
    maxWidth: "100%",
    margin: "8px",
    padding: "16px",
    fullScreen: true,
  },
  sm: {
    maxWidth: "90%",
    margin: "16px",
    padding: "20px",
    fullScreen: false,
  },
  md: {
    maxWidth: "600px",
    margin: "24px",
    padding: "24px",
    fullScreen: false,
  },
  lg: {
    maxWidth: "800px",
    margin: "32px",
    padding: "32px",
    fullScreen: false,
  },
  xl: {
    maxWidth: "1000px",
    margin: "40px",
    padding: "40px",
    fullScreen: false,
  },
} as const;

// === HOOKS DE BREAKPOINTS ===

/**
 * Configuración para useMediaQuery de MUI
 */
export const muiBreakpoints = {
  up: (key: keyof typeof breakpoints) => `(min-width:${breakpoints[key]}px)`,
  down: (key: keyof typeof breakpoints) =>
    `(max-width:${breakpoints[key] - 1}px)`,
  between: (start: keyof typeof breakpoints, end: keyof typeof breakpoints) =>
    `(min-width:${breakpoints[start]}px) and (max-width:${
      breakpoints[end] - 1
    }px)`,
} as const;

// === CONSTANTES DE BREAKPOINTS ===
export const BREAKPOINT_VALUES = {
  xs: breakpointTokens.xs,
  sm: breakpointTokens.sm,
  md: breakpointTokens.md,
  lg: breakpointTokens.lg,
  xl: breakpointTokens.xl,
} as const;

export const RESPONSIVE_CONSTANTS = {
  mobileMaxWidth: breakpointTokens.sm - 1,
  tabletMinWidth: breakpointTokens.sm,
  tabletMaxWidth: breakpointTokens.md - 1,
  desktopMinWidth: breakpointTokens.md,
  largeDesktopMinWidth: breakpointTokens.lg,
} as const;
