/**
 * 🎨 Typography System - Universal Camera Viewer
 * Sistema de tipografía completo
 */

import { typographyTokens } from "./tokens";

// === DEFINICIONES DE TIPOGRAFÍA ===
export const typography = {
  // Familia de fuentes
  fontFamily: {
    primary: typographyTokens.fontFamily.primary,
    mono: typographyTokens.fontFamily.mono,
  },

  // Variantes de texto
  variants: {
    // Títulos principales
    h1: {
      fontSize: typographyTokens.fontSize["4xl"],
      fontWeight: typographyTokens.fontWeight.bold,
      lineHeight: typographyTokens.lineHeight.tight,
      letterSpacing: "-0.025em",
    },

    h2: {
      fontSize: typographyTokens.fontSize["3xl"],
      fontWeight: typographyTokens.fontWeight.bold,
      lineHeight: typographyTokens.lineHeight.tight,
      letterSpacing: "-0.025em",
    },

    h3: {
      fontSize: typographyTokens.fontSize["2xl"],
      fontWeight: typographyTokens.fontWeight.semiBold,
      lineHeight: typographyTokens.lineHeight.tight,
    },

    h4: {
      fontSize: typographyTokens.fontSize.xl,
      fontWeight: typographyTokens.fontWeight.semiBold,
      lineHeight: typographyTokens.lineHeight.tight,
    },

    h5: {
      fontSize: typographyTokens.fontSize.lg,
      fontWeight: typographyTokens.fontWeight.medium,
      lineHeight: typographyTokens.lineHeight.normal,
    },

    h6: {
      fontSize: typographyTokens.fontSize.base,
      fontWeight: typographyTokens.fontWeight.medium,
      lineHeight: typographyTokens.lineHeight.normal,
    },

    // Texto de párrafo
    body1: {
      fontSize: typographyTokens.fontSize.base,
      fontWeight: typographyTokens.fontWeight.normal,
      lineHeight: typographyTokens.lineHeight.normal,
    },

    body2: {
      fontSize: typographyTokens.fontSize.sm,
      fontWeight: typographyTokens.fontWeight.normal,
      lineHeight: typographyTokens.lineHeight.normal,
    },

    // Texto pequeño
    caption: {
      fontSize: typographyTokens.fontSize.xs,
      fontWeight: typographyTokens.fontWeight.normal,
      lineHeight: typographyTokens.lineHeight.normal,
    },

    // Texto de botones
    button: {
      fontSize: typographyTokens.fontSize.sm,
      fontWeight: typographyTokens.fontWeight.medium,
      lineHeight: typographyTokens.lineHeight.tight,
      textTransform: "none" as const,
    },

    // Texto de labels
    label: {
      fontSize: typographyTokens.fontSize.sm,
      fontWeight: typographyTokens.fontWeight.medium,
      lineHeight: typographyTokens.lineHeight.normal,
    },

    // Texto monoespaciado (IPs, códigos)
    mono: {
      fontFamily: typographyTokens.fontFamily.mono,
      fontSize: typographyTokens.fontSize.sm,
      fontWeight: typographyTokens.fontWeight.normal,
      lineHeight: typographyTokens.lineHeight.normal,
    },
  },

  // Variantes específicas para cámaras
  camera: {
    // Nombre de cámara
    name: {
      fontSize: typographyTokens.fontSize.base,
      fontWeight: typographyTokens.fontWeight.medium,
      lineHeight: typographyTokens.lineHeight.tight,
    },

    // IP de cámara
    ip: {
      fontFamily: typographyTokens.fontFamily.mono,
      fontSize: typographyTokens.fontSize.sm,
      fontWeight: typographyTokens.fontWeight.normal,
      lineHeight: typographyTokens.lineHeight.normal,
    },

    // Estado de cámara
    status: {
      fontSize: typographyTokens.fontSize.xs,
      fontWeight: typographyTokens.fontWeight.medium,
      lineHeight: typographyTokens.lineHeight.tight,
      textTransform: "uppercase" as const,
    },

    // Métricas de streaming
    metrics: {
      fontFamily: typographyTokens.fontFamily.mono,
      fontSize: typographyTokens.fontSize.xs,
      fontWeight: typographyTokens.fontWeight.normal,
      lineHeight: typographyTokens.lineHeight.normal,
    },
  },
} as const;

// === FUNCIONES UTILITARIAS ===

/**
 * Genera estilos CSS para una variante de tipografía
 */
export function getTypographyStyles(variant: keyof typeof typography.variants) {
  return typography.variants[variant];
}

/**
 * Genera estilos CSS para tipografía de cámaras
 */
export function getCameraTypographyStyles(
  variant: keyof typeof typography.camera
) {
  return typography.camera[variant];
}

/**
 * Trunca texto con ellipsis
 */
export function truncateText(maxLines: number = 1) {
  if (maxLines === 1) {
    return {
      overflow: "hidden",
      textOverflow: "ellipsis",
      whiteSpace: "nowrap" as const,
    };
  }

  return {
    overflow: "hidden",
    textOverflow: "ellipsis",
    display: "-webkit-box",
    WebkitLineClamp: maxLines,
    WebkitBoxOrient: "vertical" as const,
  };
}

// === CONSTANTES DE TIPOGRAFÍA ===
export const FONT_WEIGHTS = {
  light: typographyTokens.fontWeight.light,
  normal: typographyTokens.fontWeight.normal,
  medium: typographyTokens.fontWeight.medium,
  semiBold: typographyTokens.fontWeight.semiBold,
  bold: typographyTokens.fontWeight.bold,
} as const;

export const FONT_SIZES = {
  xs: typographyTokens.fontSize.xs,
  sm: typographyTokens.fontSize.sm,
  base: typographyTokens.fontSize.base,
  lg: typographyTokens.fontSize.lg,
  xl: typographyTokens.fontSize.xl,
  "2xl": typographyTokens.fontSize["2xl"],
  "3xl": typographyTokens.fontSize["3xl"],
  "4xl": typographyTokens.fontSize["4xl"],
  "5xl": typographyTokens.fontSize["5xl"],
} as const;

export const LINE_HEIGHTS = {
  tight: typographyTokens.lineHeight.tight,
  normal: typographyTokens.lineHeight.normal,
  relaxed: typographyTokens.lineHeight.relaxed,
} as const;
