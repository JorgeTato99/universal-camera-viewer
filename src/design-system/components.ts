/**
 * 🎨 Component Styles - Universal Camera Viewer
 * Estilos específicos para componentes del sistema
 */

import {
  colorTokens,
  shadowTokens,
  borderTokens,
  spacingTokens,
} from "./tokens";

// === ESTILOS DE BOTONES ===
export const buttonStyles = {
  primary: {
    backgroundColor: colorTokens.primary[500],
    color: "#ffffff",
    "&:hover": {
      backgroundColor: colorTokens.primary[600],
    },
    "&:active": {
      backgroundColor: colorTokens.primary[700],
    },
    "&:disabled": {
      backgroundColor: colorTokens.neutral[300],
      color: colorTokens.neutral[500],
    },
  },

  secondary: {
    backgroundColor: colorTokens.secondary[500],
    color: "#ffffff",
    "&:hover": {
      backgroundColor: colorTokens.secondary[600],
    },
    "&:active": {
      backgroundColor: colorTokens.secondary[700],
    },
  },

  outlined: {
    backgroundColor: "transparent",
    color: colorTokens.primary[500],
    border: `1px solid ${colorTokens.primary[500]}`,
    "&:hover": {
      backgroundColor: colorTokens.primary[50],
    },
  },

  text: {
    backgroundColor: "transparent",
    color: colorTokens.primary[500],
    "&:hover": {
      backgroundColor: colorTokens.primary[50],
    },
  },

  // Botones específicos para estados de cámaras
  connect: {
    backgroundColor: colorTokens.status.connected,
    color: "#ffffff",
    "&:hover": {
      backgroundColor: colorTokens.secondary[600],
    },
  },

  disconnect: {
    backgroundColor: colorTokens.status.error,
    color: "#ffffff",
    "&:hover": {
      backgroundColor: colorTokens.alert.error,
    },
  },
} as const;

// === ESTILOS DE CARDS ===
export const cardStyles = {
  default: {
    backgroundColor: (theme: any) => theme.palette.background.paper,
    borderRadius: borderTokens.radius.base, // Más cuadrado como VS Code
    boxShadow: shadowTokens.md,
    padding: spacingTokens.md,
    border: (theme: any) => `1px solid ${theme.palette.divider}`,
  },

  elevated: {
    backgroundColor: (theme: any) =>
      theme.palette.mode === "dark"
        ? colorTokens.background.darkElevated
        : colorTokens.background.lightElevated,
    borderRadius: borderTokens.radius.base, // Más cuadrado como VS Code
    boxShadow: shadowTokens.lg,
    padding: spacingTokens.lg,
    border: "none",
  },

  // Card específico para cámaras
  camera: {
    backgroundColor: (theme: any) =>
      theme.palette.mode === "dark"
        ? colorTokens.background.darkElevated
        : colorTokens.background.lightElevated,
    borderRadius: borderTokens.radius.base, // Más cuadrado como VS Code
    boxShadow: shadowTokens.base,
    padding: spacingTokens.sm,
    border: (theme: any) => `1px solid ${theme.palette.divider}`,
    transition: "all 0.2s ease",
    "&:hover": {
      boxShadow: shadowTokens.lg,
      transform: "translateY(-2px)",
    },
  },

  // Card con estado de error
  error: {
    backgroundColor: (theme: any) => theme.palette.background.paper,
    borderRadius: borderTokens.radius.base, // Más cuadrado como VS Code
    boxShadow: shadowTokens.base,
    padding: spacingTokens.md,
    border: `2px solid ${colorTokens.alert.error}`,
  },

  // Card con estado de éxito
  success: {
    backgroundColor: (theme: any) => theme.palette.background.paper,
    borderRadius: borderTokens.radius.base, // Más cuadrado como VS Code
    boxShadow: shadowTokens.base,
    padding: spacingTokens.md,
    border: `2px solid ${colorTokens.alert.success}`,
  },
} as const;

// === ESTILOS DE FORMULARIOS ===
export const formStyles = {
  container: {
    backgroundColor: (theme: any) =>
      theme.palette.mode === "dark"
        ? colorTokens.background.darkElevated
        : colorTokens.background.lightElevated,
    borderRadius: borderTokens.radius.base, // Más cuadrado como VS Code
    padding: spacingTokens.lg,
    boxShadow: shadowTokens.base,
  },

  field: {
    marginBottom: spacingTokens.md,
    "& .MuiOutlinedInput-root": {
      borderRadius: borderTokens.radius.base, // Más cuadrado como VS Code
      "& fieldset": {
        borderColor: (theme: any) => theme.palette.divider,
      },
      "&:hover fieldset": {
        borderColor: (theme: any) => theme.palette.text.secondary,
      },
      "&.Mui-focused fieldset": {
        borderColor: (theme: any) => theme.palette.primary.main,
        borderWidth: "2px",
      },
    },
  },

  label: {
    color: (theme: any) => theme.palette.text.primary,
    fontSize: "0.875rem",
    fontWeight: 500,
    marginBottom: spacingTokens.xs,
  },

  error: {
    color: colorTokens.alert.error,
    fontSize: "0.75rem",
    marginTop: spacingTokens.xs,
  },
} as const;

// === ESTILOS DE NAVEGACIÓN ===
export const navigationStyles = {
  sidebar: {
    backgroundColor: colorTokens.background.paper,
    borderRight: `1px solid ${colorTokens.neutral[200]}`,
    padding: spacingTokens.md,
    width: "280px",
    height: "100vh",
    position: "fixed" as const,
    left: 0,
    top: 0,
    zIndex: 1000,
  },

  topbar: {
    backgroundColor: colorTokens.primary[500],
    color: "#ffffff",
    padding: `${spacingTokens.sm} ${spacingTokens.md}`,
    boxShadow: shadowTokens.md,
    position: "sticky" as const,
    top: 0,
    zIndex: 1100,
  },

  menuItem: {
    padding: `${spacingTokens.sm} ${spacingTokens.md}`,
    borderRadius: borderTokens.radius.md,
    color: colorTokens.neutral[700],
    textDecoration: "none",
    display: "flex",
    alignItems: "center",
    gap: spacingTokens.sm,
    "&:hover": {
      backgroundColor: colorTokens.primary[50],
      color: colorTokens.primary[700],
    },
    "&.active": {
      backgroundColor: colorTokens.primary[100],
      color: colorTokens.primary[700],
      fontWeight: 500,
    },
  },
} as const;

// === ESTILOS DE ESTADOS ===
export const statusStyles = {
  connected: {
    color: colorTokens.status.connected,
    backgroundColor: `${colorTokens.status.connected}20`,
    padding: `${spacingTokens.xs} ${spacingTokens.sm}`,
    borderRadius: borderTokens.radius.full,
    fontSize: "0.75rem",
    fontWeight: 500,
    textTransform: "uppercase" as const,
  },

  connecting: {
    color: colorTokens.status.connecting,
    backgroundColor: `${colorTokens.status.connecting}20`,
    padding: `${spacingTokens.xs} ${spacingTokens.sm}`,
    borderRadius: borderTokens.radius.full,
    fontSize: "0.75rem",
    fontWeight: 500,
    textTransform: "uppercase" as const,
  },

  disconnected: {
    color: colorTokens.status.disconnected,
    backgroundColor: `${colorTokens.status.disconnected}20`,
    padding: `${spacingTokens.xs} ${spacingTokens.sm}`,
    borderRadius: borderTokens.radius.full,
    fontSize: "0.75rem",
    fontWeight: 500,
    textTransform: "uppercase" as const,
  },

  streaming: {
    color: colorTokens.status.streaming,
    backgroundColor: `${colorTokens.status.streaming}20`,
    padding: `${spacingTokens.xs} ${spacingTokens.sm}`,
    borderRadius: borderTokens.radius.full,
    fontSize: "0.75rem",
    fontWeight: 500,
    textTransform: "uppercase" as const,
  },

  error: {
    color: colorTokens.status.error,
    backgroundColor: `${colorTokens.status.error}20`,
    padding: `${spacingTokens.xs} ${spacingTokens.sm}`,
    borderRadius: borderTokens.radius.full,
    fontSize: "0.75rem",
    fontWeight: 500,
    textTransform: "uppercase" as const,
  },

  unavailable: {
    color: colorTokens.status.unavailable,
    backgroundColor: `${colorTokens.status.unavailable}20`,
    padding: `${spacingTokens.xs} ${spacingTokens.sm}`,
    borderRadius: borderTokens.radius.full,
    fontSize: "0.75rem",
    fontWeight: 500,
    textTransform: "uppercase" as const,
  },
} as const;

// === ESTILOS DE MODAL ===
export const modalStyles = {
  overlay: {
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    position: "fixed" as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 9999,
  },

  content: {
    backgroundColor: colorTokens.background.paper,
    borderRadius: borderTokens.radius.base, // Más cuadrado como VS Code
    padding: spacingTokens.lg,
    maxWidth: "600px",
    width: "90%",
    maxHeight: "90vh",
    position: "absolute" as const,
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    boxShadow: shadowTokens.xl,
  },

  header: {
    borderBottom: `1px solid ${colorTokens.neutral[200]}`,
    paddingBottom: spacingTokens.md,
    marginBottom: spacingTokens.md,
  },

  footer: {
    borderTop: `1px solid ${colorTokens.neutral[200]}`,
    paddingTop: spacingTokens.md,
    marginTop: spacingTokens.md,
    display: "flex",
    justifyContent: "flex-end",
    gap: spacingTokens.sm,
  },
} as const;

// === ESTILOS DE GRID ===
export const gridStyles = {
  container: {
    display: "grid",
    gap: spacingTokens.md,
    padding: spacingTokens.md,
  },

  cameraGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
    gap: spacingTokens.md,
    padding: spacingTokens.md,
  },

  responsiveGrid: {
    display: "grid",
    gap: spacingTokens.md,
    padding: spacingTokens.md,
    "@media (min-width: 600px)": {
      gridTemplateColumns: "repeat(2, 1fr)",
    },
    "@media (min-width: 900px)": {
      gridTemplateColumns: "repeat(3, 1fr)",
    },
    "@media (min-width: 1200px)": {
      gridTemplateColumns: "repeat(4, 1fr)",
    },
  },
} as const;

// === ANIMACIONES ===
export const animations = {
  fadeIn: {
    "@keyframes fadeIn": {
      from: { opacity: 0 },
      to: { opacity: 1 },
    },
    animation: "fadeIn 0.3s ease-in-out",
  },

  slideIn: {
    "@keyframes slideIn": {
      from: { transform: "translateX(-100%)" },
      to: { transform: "translateX(0)" },
    },
    animation: "slideIn 0.3s ease-in-out",
  },

  pulse: {
    "@keyframes pulse": {
      "0%, 100%": { opacity: 1 },
      "50%": { opacity: 0.5 },
    },
    animation: "pulse 1s ease-in-out infinite",
  },
} as const;
