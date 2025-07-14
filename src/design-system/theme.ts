/**
 * 🎨 Theme Configuration - Universal Camera Viewer
 * Configuración del tema Material-UI con tokens del design system
 */

import { createTheme, ThemeOptions } from "@mui/material/styles";
import {
  colorTokens,
  typographyTokens,
  spacingTokens,
  borderTokens,
  shadowTokens,
  breakpointTokens,
} from "./tokens";

// === CONFIGURACIÓN BASE DEL TEMA ===
const baseThemeOptions: ThemeOptions = {
  // Configuración de breakpoints
  breakpoints: {
    values: {
      xs: breakpointTokens.xs,
      sm: breakpointTokens.sm,
      md: breakpointTokens.md,
      lg: breakpointTokens.lg,
      xl: breakpointTokens.xl,
    },
  },

  // Configuración de espaciado
  spacing: 8, // Base de 8px

  // Configuración de forma
  shape: {
    borderRadius: parseInt(borderTokens.radius.md.replace("rem", "")) * 16, // Convertir rem a px
  },

  // Configuración de tipografía
  typography: {
    fontFamily: typographyTokens.fontFamily.primary,
    h1: {
      fontSize: typographyTokens.fontSize["4xl"],
      fontWeight: typographyTokens.fontWeight.bold,
      lineHeight: typographyTokens.lineHeight.tight,
    },
    h2: {
      fontSize: typographyTokens.fontSize["3xl"],
      fontWeight: typographyTokens.fontWeight.bold,
      lineHeight: typographyTokens.lineHeight.tight,
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
    caption: {
      fontSize: typographyTokens.fontSize.xs,
      fontWeight: typographyTokens.fontWeight.normal,
      lineHeight: typographyTokens.lineHeight.normal,
    },
    button: {
      fontSize: typographyTokens.fontSize.sm,
      fontWeight: typographyTokens.fontWeight.medium,
      lineHeight: typographyTokens.lineHeight.tight,
      textTransform: "none",
    },
  },

  // Configuración de componentes
  components: {
    // Configuración de botones
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: borderTokens.radius.base, // Más cuadrado como VS Code
          textTransform: "none",
          padding: `${spacingTokens.sm} ${spacingTokens.md}`,
          fontSize: typographyTokens.fontSize.sm,
          fontWeight: typographyTokens.fontWeight.medium,
          minHeight: "40px",
          boxShadow: "none",
          "&:hover": {
            boxShadow: shadowTokens.base,
          },
        },
      },
    },

    // Configuración de cards
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: borderTokens.radius.base, // Más cuadrado como VS Code
          boxShadow: shadowTokens.base,
          border: `1px solid ${colorTokens.neutral[200]}`,
          "&:hover": {
            boxShadow: shadowTokens.md,
          },
        },
      },
    },

    // Configuración de inputs
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: borderTokens.radius.base, // Más cuadrado como VS Code
          "& .MuiOutlinedInput-notchedOutline": {
            borderColor: colorTokens.neutral[300],
          },
          "&:hover .MuiOutlinedInput-notchedOutline": {
            borderColor: colorTokens.neutral[400],
          },
          "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
            borderColor: colorTokens.primary[500],
            borderWidth: "2px",
          },
        },
      },
    },

    // Configuración de AppBar
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: shadowTokens.md,
          borderBottom: `1px solid ${colorTokens.neutral[200]}`,
        },
      },
    },

    // Configuración de Paper
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: borderTokens.radius.base, // Más cuadrado como VS Code
          boxShadow: shadowTokens.base,
        },
      },
    },

    // Configuración de Chip
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: borderTokens.radius.full,
          fontSize: typographyTokens.fontSize.xs,
          fontWeight: typographyTokens.fontWeight.medium,
          textTransform: "uppercase",
        },
      },
    },

    // Configuración de Drawer
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRadius: 0,
          boxShadow: shadowTokens.lg,
        },
      },
    },
  },
};

// === TEMA MODO CLARO ===
export const lightTheme = createTheme({
  ...baseThemeOptions,
  palette: {
    mode: "light",
    primary: {
      main: colorTokens.primary[500],
      light: colorTokens.primary[300],
      dark: colorTokens.primary[700],
      contrastText: "#ffffff",
    },
    secondary: {
      main: colorTokens.secondary[500],
      light: colorTokens.secondary[300],
      dark: colorTokens.secondary[700],
      contrastText: "#ffffff",
    },
    error: {
      main: colorTokens.alert.error,
      light: colorTokens.alert.error,
      dark: colorTokens.alert.error,
      contrastText: "#ffffff",
    },
    warning: {
      main: colorTokens.alert.warning,
      light: colorTokens.alert.warning,
      dark: colorTokens.alert.warning,
      contrastText: "#ffffff",
    },
    info: {
      main: colorTokens.alert.info,
      light: colorTokens.alert.info,
      dark: colorTokens.alert.info,
      contrastText: "#ffffff",
    },
    success: {
      main: colorTokens.alert.success,
      light: colorTokens.alert.success,
      dark: colorTokens.alert.success,
      contrastText: "#ffffff",
    },
    background: {
      default: colorTokens.background.light, // Nivel 3: Fondo principal
      paper: colorTokens.background.lightElevated, // Para elementos elevados
    },
    text: {
      primary: colorTokens.neutral[900],
      secondary: colorTokens.neutral[600],
      disabled: colorTokens.neutral[400],
    },
    divider: colorTokens.neutral[200],
    action: {
      hover: colorTokens.neutral[50],
      selected: colorTokens.primary[50],
      disabled: colorTokens.neutral[300],
    },
  },
});

// === TEMA MODO OSCURO ===
export const darkTheme = createTheme({
  ...baseThemeOptions,
  palette: {
    mode: "dark",
    primary: {
      main: colorTokens.primary[400],
      light: colorTokens.primary[300],
      dark: colorTokens.primary[600],
      contrastText: colorTokens.neutral[900],
    },
    secondary: {
      main: colorTokens.secondary[400],
      light: colorTokens.secondary[300],
      dark: colorTokens.secondary[600],
      contrastText: colorTokens.neutral[900],
    },
    error: {
      main: colorTokens.alert.error,
      light: colorTokens.alert.error,
      dark: colorTokens.alert.error,
      contrastText: "#ffffff",
    },
    warning: {
      main: colorTokens.alert.warning,
      light: colorTokens.alert.warning,
      dark: colorTokens.alert.warning,
      contrastText: "#ffffff",
    },
    info: {
      main: colorTokens.alert.info,
      light: colorTokens.alert.info,
      dark: colorTokens.alert.info,
      contrastText: "#ffffff",
    },
    success: {
      main: colorTokens.alert.success,
      light: colorTokens.alert.success,
      dark: colorTokens.alert.success,
      contrastText: "#ffffff",
    },
    background: {
      default: colorTokens.background.dark, // Nivel 3: Fondo principal
      paper: colorTokens.background.darkElevated, // Para elementos elevados
    },
    text: {
      primary: colorTokens.neutral[50],
      secondary: colorTokens.neutral[300],
      disabled: colorTokens.neutral[600],
    },
    divider: colorTokens.neutral[700],
    action: {
      hover: colorTokens.neutral[700], // Más sutil para hover
      selected: colorTokens.primary[800], // Menos intenso
      disabled: colorTokens.neutral[600],
    },
  },
});

// === FUNCIÓN PARA OBTENER TEMA ===
export function getTheme(mode: "light" | "dark" = "light") {
  return mode === "dark" ? darkTheme : lightTheme;
}

// === COLORES CUSTOMIZADOS PARA ESTADOS DE CÁMARAS ===
export const cameraStatusColors = {
  connected: colorTokens.status.connected,
  connecting: colorTokens.status.connecting,
  disconnected: colorTokens.status.disconnected,
  streaming: colorTokens.status.streaming,
  error: colorTokens.status.error,
  unavailable: colorTokens.status.unavailable,
};

// === ESTILOS CUSTOMIZADOS PARA MATERIAL-UI ===
export const muiCustomStyles = {
  // Estilo para status chips
  statusChip: {
    borderRadius: borderTokens.radius.full,
    fontSize: typographyTokens.fontSize.xs,
    fontWeight: typographyTokens.fontWeight.medium,
    textTransform: "uppercase",
    padding: `${spacingTokens.xs} ${spacingTokens.sm}`,
  },

  // Estilo para cards de cámaras
  cameraCard: {
    borderRadius: borderTokens.radius.lg,
    boxShadow: shadowTokens.base,
    padding: spacingTokens.sm,
    border: `1px solid ${colorTokens.neutral[200]}`,
    transition: "all 0.2s ease",
    "&:hover": {
      boxShadow: shadowTokens.lg,
      transform: "translateY(-2px)",
    },
  },

  // Estilo para formularios
  formContainer: {
    backgroundColor: colorTokens.background.paper,
    borderRadius: borderTokens.radius.lg,
    padding: spacingTokens.lg,
    boxShadow: shadowTokens.base,
  },

  // Estilo para sidebar
  sidebar: {
    backgroundColor: colorTokens.background.paper,
    borderRight: `1px solid ${colorTokens.neutral[200]}`,
    width: "280px",
    height: "100vh",
  },
};

// === TEMA POR DEFECTO ===
export const defaultTheme = lightTheme;

// === CONFIGURACIÓN EXTENDIDA ===
export const extendedTheme = {
  ...lightTheme,
  custom: {
    colors: colorTokens,
    typography: typographyTokens,
    spacing: spacingTokens,
    borders: borderTokens,
    shadows: shadowTokens,
    breakpoints: breakpointTokens,
    cameraStatus: cameraStatusColors,
    styles: muiCustomStyles,
  },
};
