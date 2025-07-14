/**
 * 🎨 Design Tokens - Universal Camera Viewer
 * Tokens fundamentales del sistema de diseño
 */

// === PALETA DE COLORES ===
export const colorTokens = {
  // Colores primarios - Azul tecnológico
  primary: {
    50: "#e3f2fd",
    100: "#bbdefb",
    200: "#90caf9",
    300: "#64b5f6",
    400: "#42a5f5",
    500: "#2196f3", // Color principal
    600: "#1e88e5",
    700: "#1976d2",
    800: "#1565c0",
    900: "#0d47a1",
  },

  // Colores secundarios - Verde success/conexión
  secondary: {
    50: "#e8f5e8",
    100: "#c8e6c9",
    200: "#a5d6a7",
    300: "#81c784",
    400: "#66bb6a",
    500: "#4caf50", // Verde principal
    600: "#43a047",
    700: "#388e3c",
    800: "#2e7d32",
    900: "#1b5e20",
  },

  // Estados de cámaras
  status: {
    connected: "#4caf50",
    connecting: "#ff9800",
    disconnected: "#f44336",
    streaming: "#2196f3",
    error: "#f44336",
    unavailable: "#9e9e9e",
  },

  // Grises neutros
  neutral: {
    50: "#fafafa",
    100: "#f5f5f5",
    200: "#eeeeee",
    300: "#e0e0e0",
    400: "#bdbdbd",
    500: "#9e9e9e",
    600: "#757575",
    700: "#616161",
    800: "#424242",
    900: "#212121",
  },

  // Colores de fondo - Jerarquía de 3 niveles
  background: {
    // Modo claro - Jerarquía de 3 niveles
    light: "#fafafa", // Nivel 3: Fondo principal claro
    paper: "#ffffff", // Elementos paper claros
    surface: "#f8f9fa", // Nivel 1: TopBar (más claro)
    lightSidebar: "#f5f5f5", // Nivel 2: Sidebar (intermedio)
    lightElevated: "#ffffff", // Para elementos elevados

    // Modo oscuro - Jerarquía de 3 niveles
    dark: "#2a2a2a", // Nivel 3: Fondo principal (más claro)
    darkPaper: "#1a1a1a", // Nivel 2: Sidebar (intermedio)
    darkSurface: "#121212", // Nivel 1: TopBar (más oscuro)
    darkElevated: "#363636", // Para elementos elevados sobre fondo principal
  },

  // Colores de alerta
  alert: {
    error: "#f44336",
    warning: "#ff9800",
    info: "#2196f3",
    success: "#4caf50",
  },
};

// === TIPOGRAFÍA ===
export const typographyTokens = {
  fontFamily: {
    primary: '"Roboto", "Helvetica", "Arial", sans-serif',
    mono: '"Roboto Mono", "Consolas", "Monaco", monospace',
  },

  fontSize: {
    xs: "0.75rem", // 12px
    sm: "0.875rem", // 14px
    base: "1rem", // 16px
    lg: "1.125rem", // 18px
    xl: "1.25rem", // 20px
    "2xl": "1.5rem", // 24px
    "3xl": "1.875rem", // 30px
    "4xl": "2.25rem", // 36px
    "5xl": "3rem", // 48px
  },

  fontWeight: {
    light: 300,
    normal: 400,
    medium: 500,
    semiBold: 600,
    bold: 700,
  },

  lineHeight: {
    tight: 1.2,
    normal: 1.5,
    relaxed: 1.6,
  },
};

// === ESPACIADO ===
export const spacingTokens = {
  xs: "0.25rem", // 4px
  sm: "0.5rem", // 8px
  md: "1rem", // 16px
  lg: "1.5rem", // 24px
  xl: "2rem", // 32px
  "2xl": "3rem", // 48px
  "3xl": "4rem", // 64px
  "4xl": "6rem", // 96px
};

// === BREAKPOINTS ===
export const breakpointTokens = {
  xs: 0,
  sm: 600,
  md: 900,
  lg: 1200,
  xl: 1536,
};

// === SOMBRAS ===
export const shadowTokens = {
  none: "none",
  sm: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
  base: "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
  md: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
  lg: "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
  xl: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",

  // Sombras para modo oscuro
  dark: {
    none: "none",
    sm: "0 1px 2px 0 rgba(0, 0, 0, 0.2)",
    base: "0 1px 3px 0 rgba(0, 0, 0, 0.3), 0 1px 2px 0 rgba(0, 0, 0, 0.2)",
    md: "0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)",
    lg: "0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3)",
    xl: "0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.4)",
  },
};

// === BORDES ===
export const borderTokens = {
  radius: {
    none: "0",
    sm: "0.125rem", // 2px - Solo para elementos muy pequeños
    base: "0.125rem", // 2px - Mínimo redondeado para consistencia
    md: "0.25rem", // 4px - Solo para elementos especiales
    lg: "0.25rem", // 4px - Máximo redondeado general
    xl: "0.375rem", // 6px - Solo para elementos destacados
    "2xl": "0.5rem", // 8px - Solo para elementos muy especiales
    full: "9999px", // Para elementos circulares (badges, etc.)
  },

  width: {
    thin: "1px",
    base: "2px",
    thick: "4px",
  },
};

// === ANIMACIONES ===
export const animationTokens = {
  duration: {
    fast: "150ms",
    base: "300ms",
    slow: "500ms",
  },

  easing: {
    linear: "linear",
    easeIn: "cubic-bezier(0.4, 0, 1, 1)",
    easeOut: "cubic-bezier(0, 0, 0.2, 1)",
    easeInOut: "cubic-bezier(0.4, 0, 0.2, 1)",
  },
};

// === Z-INDEX ===
export const zIndexTokens = {
  hide: -1,
  base: 0,
  dropdown: 1000,
  sticky: 1020,
  fixed: 1030,
  modal: 1040,
  popover: 1050,
  tooltip: 1060,
  overlay: 1070,
  max: 2147483647,
};

// Token consolidado
export const designTokens = {
  colors: colorTokens,
  typography: typographyTokens,
  spacing: spacingTokens,
  breakpoints: breakpointTokens,
  shadows: shadowTokens,
  borders: borderTokens,
  animation: animationTokens,
  zIndex: zIndexTokens,
} as const;
