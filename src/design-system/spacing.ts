/**
 * 🎨 Spacing System - Universal Camera Viewer
 * Sistema de espaciado y layout
 */

import { spacingTokens } from "./tokens";

// === VALORES DE ESPACIADO ===
export const spacing = {
  xs: spacingTokens.xs, // 4px
  sm: spacingTokens.sm, // 8px
  md: spacingTokens.md, // 16px
  lg: spacingTokens.lg, // 24px
  xl: spacingTokens.xl, // 32px
  "2xl": spacingTokens["2xl"], // 48px
  "3xl": spacingTokens["3xl"], // 64px
  "4xl": spacingTokens["4xl"], // 96px
} as const;

// === FUNCIONES UTILITARIAS ===

/**
 * Genera estilos de padding
 */
export function getPadding(
  value: keyof typeof spacing | number,
  sides?: "x" | "y" | "top" | "bottom" | "left" | "right"
) {
  const paddingValue =
    typeof value === "number" ? `${value}px` : spacing[value];

  switch (sides) {
    case "x":
      return {
        paddingLeft: paddingValue,
        paddingRight: paddingValue,
      };
    case "y":
      return {
        paddingTop: paddingValue,
        paddingBottom: paddingValue,
      };
    case "top":
      return { paddingTop: paddingValue };
    case "bottom":
      return { paddingBottom: paddingValue };
    case "left":
      return { paddingLeft: paddingValue };
    case "right":
      return { paddingRight: paddingValue };
    default:
      return { padding: paddingValue };
  }
}

/**
 * Genera estilos de margin
 */
export function getMargin(
  value: keyof typeof spacing | number,
  sides?: "x" | "y" | "top" | "bottom" | "left" | "right"
) {
  const marginValue = typeof value === "number" ? `${value}px` : spacing[value];

  switch (sides) {
    case "x":
      return {
        marginLeft: marginValue,
        marginRight: marginValue,
      };
    case "y":
      return {
        marginTop: marginValue,
        marginBottom: marginValue,
      };
    case "top":
      return { marginTop: marginValue };
    case "bottom":
      return { marginBottom: marginValue };
    case "left":
      return { marginLeft: marginValue };
    case "right":
      return { marginRight: marginValue };
    default:
      return { margin: marginValue };
  }
}

/**
 * Genera estilos de gap para flexbox/grid
 */
export function getGap(value: keyof typeof spacing | number) {
  const gapValue = typeof value === "number" ? `${value}px` : spacing[value];
  return { gap: gapValue };
}

// === LAYOUTS PREDEFINIDOS ===

/**
 * Layout para grids de cámaras
 */
export const cameraGridLayout = {
  container: {
    ...getPadding("md"),
    ...getGap("md"),
  },

  item: {
    ...getPadding("sm"),
    ...getMargin("xs", "bottom"),
  },

  compact: {
    ...getPadding("sm"),
    ...getGap("sm"),
  },
} as const;

/**
 * Layout para formularios
 */
export const formLayout = {
  container: {
    ...getPadding("lg"),
    ...getGap("md"),
  },

  field: {
    ...getMargin("sm", "bottom"),
  },

  group: {
    ...getMargin("md", "bottom"),
  },

  actions: {
    ...getMargin("lg", "top"),
    ...getPadding("md", "top"),
    ...getGap("sm"),
  },
} as const;

/**
 * Layout para navegación
 */
export const navigationLayout = {
  sidebar: {
    ...getPadding("md"),
    ...getGap("sm"),
  },

  topbar: {
    ...getPadding("sm", "x"),
    ...getPadding("xs", "y"),
  },

  menu: {
    ...getPadding("xs"),
    ...getGap("xs"),
  },
} as const;

/**
 * Layout para contenido principal
 */
export const contentLayout = {
  page: {
    ...getPadding("lg"),
    ...getMargin("md", "bottom"),
  },

  section: {
    ...getMargin("lg", "bottom"),
  },

  card: {
    ...getPadding("md"),
  },

  modal: {
    ...getPadding("lg"),
    ...getGap("md"),
  },
} as const;

// === CONSTANTES DE ESPACIADO ===
export const SPACING_VALUES = {
  xs: spacingTokens.xs,
  sm: spacingTokens.sm,
  md: spacingTokens.md,
  lg: spacingTokens.lg,
  xl: spacingTokens.xl,
  "2xl": spacingTokens["2xl"],
  "3xl": spacingTokens["3xl"],
  "4xl": spacingTokens["4xl"],
} as const;

export const LAYOUT_CONSTANTS = {
  sidebarWidth: "280px",
  topbarHeight: "64px",
  bottombarHeight: "48px",
  cardMinHeight: "200px",
  modalMaxWidth: "600px",
} as const;
