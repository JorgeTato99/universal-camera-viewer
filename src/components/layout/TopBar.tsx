/**
 * 🎯 TopBar Component - Universal Camera Viewer
 * Barra superior fija similar a VS Code
 */

import React, { useState } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  alpha,
  useTheme as useMuiTheme,
  Tooltip,
  Badge,
} from "@mui/material";
import {
  Menu as MenuIcon,
  Settings as SettingsIcon,
  Help as HelpIcon,
  Minimize,
  CropSquare,
  Close,
} from "@mui/icons-material";
import { useTheme } from "../../hooks/useTheme";
import { ThemeToggle } from "../ui/ThemeToggle";
import { colorTokens } from "../../design-system/tokens";
import { AboutDialog } from "../dialogs";
import { QuickSettingsMenu } from "../menus";
import { APP_CONFIG } from "../../config/appConfig";

interface TopBarProps {
  onMenuToggle?: () => void;
  sidebarCollapsed?: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  onMenuToggle,
}) => {
  const muiTheme = useMuiTheme();
  const { effectiveTheme } = useTheme();
  const [aboutDialogOpen, setAboutDialogOpen] = useState(false);
  const [settingsAnchorEl, setSettingsAnchorEl] = useState<null | HTMLElement>(null);
  const [hasUpdate, setHasUpdate] = useState(false); 
  /**
   * 🚀 INTEGRACIÓN PENDIENTE - Indicador de Actualizaciones
   * 
   * TODO: Conectar con servicio real de actualizaciones
   * 
   * ARQUITECTURA:
   * 1. Verificar actualizaciones al iniciar la app
   * 2. Polling cada 30 minutos
   * 3. WebSocket para notificaciones push
   * 
   * IMPLEMENTACIÓN:
   * ```typescript
   * // En useEffect o custom hook
   * const checkUpdates = async () => {
   *   const hasNewVersion = await updateService.checkForUpdates();
   *   setHasUpdate(hasNewVersion);
   * };
   * 
   * // Polling
   * const interval = setInterval(checkUpdates, 30 * 60 * 1000);
   * 
   * // WebSocket
   * socket.on('update:available', () => setHasUpdate(true));
   * ```
   */

  /**
   * 🚀 INTEGRACIÓN PENDIENTE - Controles de Ventana Tauri
   * 
   * TODO: Implementar controles nativos de ventana
   * 
   * INSTALACIÓN:
   * ```bash
   * yarn add @tauri-apps/api
   * ```
   * 
   * IMPLEMENTACIÓN:
   * ```typescript
   * import { appWindow } from '@tauri-apps/api/window';
   * 
   * const handleMinimize = async () => {
   *   await appWindow.minimize();
   * };
   * 
   * const handleMaximize = async () => {
   *   await appWindow.toggleMaximize();
   * };
   * 
   * const handleClose = async () => {
   *   // Opcional: Confirmar antes de cerrar
   *   if (await confirmClose()) {
   *     await appWindow.close();
   *   }
   * };
   * ```
   * 
   * NOTA: Solo funciona en build Tauri, no en dev web
   */
  const handleMinimize = () => {
    console.log("🔧 MOCK: Minimizar ventana - REQUIERE TAURI");
  };

  const handleMaximize = () => {
    console.log("🔧 MOCK: Maximizar ventana - REQUIERE TAURI");
  };

  const handleClose = () => {
    console.log("🔧 MOCK: Cerrar ventana - REQUIERE TAURI");
  };

  const handleOpenQuickSettings = (event: React.MouseEvent<HTMLElement>) => {
    setSettingsAnchorEl(event.currentTarget);
  };

  const handleCloseQuickSettings = () => {
    setSettingsAnchorEl(null);
  };

  const quickSettingsOpen = Boolean(settingsAnchorEl);

  // Verificación de actualizaciones
  React.useEffect(() => {
    /**
     * 🔧 MOCK: Simulación de actualización disponible
     * 
     * TODO: Reemplazar con servicio real
     * Ver documentación completa en línea 47-71
     */
    const checkForUpdates = () => {
      // Simular actualización después de 5 segundos
      setTimeout(() => {
        setHasUpdate(true);
      }, 5000);
    };
    
    checkForUpdates();
  }, []);

  return (
    <>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          backgroundColor:
            effectiveTheme === "dark"
              ? colorTokens.background.darkSurface // Nivel 1: Más oscuro
              : colorTokens.background.surface, // Nivel 1: Más claro
          borderBottom: `1px solid ${
            effectiveTheme === "dark"
              ? colorTokens.background.darkPaper // Separador con nivel 2
              : colorTokens.background.lightSidebar // Separador con nivel 2
          }`,
          zIndex: muiTheme.zIndex.drawer + 1,
          height: "32px",
          minHeight: "32px",
          "& .MuiToolbar-root": {
            minHeight: "32px",
            height: "32px",
            padding: "0 8px",
          },
        }}
      >
      <Toolbar variant="dense">
        {/* Sección izquierda - Logo y menú */}
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          {/* Botón de menú hamburguesa (solo en móvil) */}
          <Tooltip title="Menú" arrow placement="right">
            <IconButton
              size="small"
              edge="start"
              color="inherit"
              onClick={onMenuToggle}
              sx={{
                display: { xs: "flex", md: "none" },
                p: 0.5,
                transition: "all 0.3s ease",
                "&:hover": {
                  backgroundColor: alpha(colorTokens.primary[500], 0.1),
                  color: colorTokens.primary[500],
                  "& svg": {
                    animation: "slideMenu 0.5s ease",
                  },
                },
                "@keyframes slideMenu": {
                  "0%, 100%": {
                    transform: "translateX(0)",
                  },
                  "50%": {
                    transform: "translateX(3px)",
                  },
                },
              }}
            >
              <MenuIcon fontSize="small" />
            </IconButton>
          </Tooltip>

          {/* Logo y título */}
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Tooltip title={APP_CONFIG.app.name} arrow placement="bottom">
              <Box
                sx={{
                  width: 16,
                  height: 16,
                  borderRadius: "50%",
                  background: `linear-gradient(45deg, ${colorTokens.primary[500]}, ${colorTokens.secondary[500]})`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "10px",
                  fontWeight: "bold",
                  color: "white",
                  cursor: "pointer",
                  transition: "all 0.3s ease",
                  "&:hover": {
                    transform: "rotate(360deg) scale(1.2)",
                    boxShadow: `0 0 8px ${alpha(colorTokens.primary[500], 0.5)}`,
                  },
                }}
              >
                {APP_CONFIG.app.shortName.charAt(0)}
              </Box>
            </Tooltip>
            <Typography
              variant="body2"
              sx={{
                color: (theme) => theme.palette.text.secondary,
                fontSize: "13px",
                fontWeight: 500,
                userSelect: "none",
              }}
            >
              {APP_CONFIG.app.name}
            </Typography>
          </Box>
        </Box>

        {/* Sección centro - Espacio flexible */}
        <Box sx={{ flexGrow: 1 }} />

        {/* Sección derecha - Controles de ventana */}
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
          {/* Controles de aplicación */}
          <ThemeToggle size="small" />

          <Tooltip title="Configuración rápida" arrow placement="bottom">
            <IconButton
              size="small"
              onClick={handleOpenQuickSettings}
              aria-describedby={quickSettingsOpen ? "quick-settings-popover" : undefined}
              sx={{
                p: 0.5,
                color: quickSettingsOpen 
                  ? colorTokens.primary[500]
                  : (theme) => theme.palette.text.secondary,
                backgroundColor: quickSettingsOpen
                  ? alpha(colorTokens.primary[500], 0.1)
                  : "transparent",
                transition: "all 0.3s ease",
                "&:hover": {
                  backgroundColor: alpha(colorTokens.primary[500], 0.1),
                  color: colorTokens.primary[500],
                  transform: "rotate(45deg)",
                },
              }}
            >
              <SettingsIcon fontSize="small" />
            </IconButton>
          </Tooltip>

          <Tooltip title={hasUpdate ? "Acerca de (¡Actualización disponible!)" : "Acerca de"} arrow placement="bottom">
            <IconButton
              size="small"
              onClick={() => setAboutDialogOpen(true)}
              sx={{
                p: 0.5,
                color: aboutDialogOpen
                  ? colorTokens.primary[500]
                  : (theme) => theme.palette.text.secondary,
                backgroundColor: aboutDialogOpen
                  ? alpha(colorTokens.primary[500], 0.1)
                  : "transparent",
                transition: "all 0.3s ease",
                "&:hover": {
                  backgroundColor: alpha(colorTokens.primary[500], 0.1),
                  color: colorTokens.primary[500],
                  transform: "scale(1.1)",
                  "& svg": {
                    animation: "pulse 1s ease-in-out",
                  },
                },
                "@keyframes pulse": {
                  "0%": {
                    transform: "scale(1)",
                  },
                  "50%": {
                    transform: "scale(1.2)",
                  },
                  "100%": {
                    transform: "scale(1)",
                  },
                },
              }}
              aria-label="Acerca de"
            >
              <Badge 
                color="error" 
                variant="dot"
                invisible={!hasUpdate}
                sx={{
                  "& .MuiBadge-dot": {
                    animation: hasUpdate ? "ripple 1.5s ease-in-out infinite" : "none",
                  },
                  "@keyframes ripple": {
                    "0%": {
                      transform: "scale(1)",
                      opacity: 1,
                    },
                    "100%": {
                      transform: "scale(2.5)",
                      opacity: 0,
                    },
                  },
                }}
              >
                <HelpIcon fontSize="small" />
              </Badge>
            </IconButton>
          </Tooltip>

          {/* Divisor */}
          <Box
            sx={{
              width: 1,
              height: 16,
              backgroundColor: colorTokens.neutral[700],
              mx: 0.5,
            }}
          />

          {/* Controles de ventana */}
          <Tooltip title="Minimizar" arrow placement="bottom">
            <IconButton
              size="small"
              onClick={handleMinimize}
              sx={{
                p: 0.5,
                color: (theme) => theme.palette.text.secondary,
                transition: "all 0.3s ease",
                "&:hover": {
                  backgroundColor: alpha(colorTokens.primary[500], 0.1),
                  color: colorTokens.primary[500],
                  transform: "translateY(2px)",
                },
              }}
            >
              <Minimize fontSize="small" />
            </IconButton>
          </Tooltip>

          <Tooltip title="Maximizar" arrow placement="bottom">
            <IconButton
              size="small"
              onClick={handleMaximize}
              sx={{
                p: 0.5,
                color: (theme) => theme.palette.text.secondary,
                transition: "all 0.3s ease",
                "&:hover": {
                  backgroundColor: alpha(colorTokens.primary[500], 0.1),
                  color: colorTokens.primary[500],
                  "& svg": {
                    transform: "rotate(180deg) scale(0.8)",
                  },
                },
              }}
            >
              <CropSquare fontSize="small" />
            </IconButton>
          </Tooltip>

          <Tooltip title="Cerrar" arrow placement="bottom">
            <IconButton
              size="small"
              onClick={handleClose}
              sx={{
                p: 0.5,
                color: (theme) => theme.palette.text.secondary,
                transition: "all 0.3s ease",
                "&:hover": {
                  backgroundColor: alpha("#f44336", 0.8),
                  color: "white",
                  transform: "rotate(90deg)",
                },
              }}
            >
              <Close fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>
      </AppBar>
      
      {/* About Dialog */}
      <AboutDialog 
        open={aboutDialogOpen} 
        onClose={() => setAboutDialogOpen(false)} 
      />
      
      {/* Quick Settings Menu */}
      <QuickSettingsMenu
        anchorEl={settingsAnchorEl}
        open={quickSettingsOpen}
        onClose={handleCloseQuickSettings}
      />
    </>
  );
};
