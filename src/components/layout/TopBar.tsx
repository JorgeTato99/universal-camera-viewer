/**
 * 🎯 TopBar Component - Universal Camera Viewer
 * Barra superior fija similar a VS Code
 */

import React from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  alpha,
  useTheme as useMuiTheme,
} from "@mui/material";
import {
  Menu as MenuIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  Help as HelpIcon,
  Minimize,
  CropSquare,
  Close,
} from "@mui/icons-material";
import { useTheme } from "../../hooks/useTheme";
import { ThemeToggle } from "../ui/ThemeToggle";
import { colorTokens } from "../../design-system/tokens";

interface TopBarProps {
  onMenuToggle?: () => void;
  sidebarCollapsed?: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  onMenuToggle,
  sidebarCollapsed = false,
}) => {
  const muiTheme = useMuiTheme();
  const { effectiveTheme } = useTheme();

  const handleMinimize = () => {
    // Implementar minimizar ventana (Tauri)
    console.log("Minimize window");
  };

  const handleMaximize = () => {
    // Implementar maximizar ventana (Tauri)
    console.log("Maximize window");
  };

  const handleClose = () => {
    // Implementar cerrar ventana (Tauri)
    console.log("Close window");
  };

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        backgroundColor:
          effectiveTheme === "dark"
            ? colorTokens.neutral[900]
            : colorTokens.neutral[800],
        borderBottom: `1px solid ${
          effectiveTheme === "dark"
            ? colorTokens.neutral[800]
            : colorTokens.neutral[700]
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
          <IconButton
            size="small"
            edge="start"
            color="inherit"
            onClick={onMenuToggle}
            sx={{
              display: { xs: "flex", md: "none" },
              p: 0.5,
              "&:hover": {
                backgroundColor: alpha(colorTokens.neutral[100], 0.1),
              },
            }}
          >
            <MenuIcon fontSize="small" />
          </IconButton>

          {/* Logo y título */}
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
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
              }}
            >
              U
            </Box>
            <Typography
              variant="body2"
              sx={{
                color: (theme) => theme.palette.text.secondary,
                fontSize: "13px",
                fontWeight: 500,
                userSelect: "none",
              }}
            >
              Universal Camera Viewer
            </Typography>
          </Box>
        </Box>

        {/* Sección centro - Espacio flexible */}
        <Box sx={{ flexGrow: 1 }} />

        {/* Sección derecha - Controles de ventana */}
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
          {/* Controles de aplicación */}
          <IconButton
            size="small"
            sx={{
              p: 0.5,
              color: (theme) => theme.palette.text.secondary,
              "&:hover": {
                backgroundColor: (theme) => theme.palette.action.hover,
                color: (theme) => theme.palette.text.primary,
              },
            }}
          >
            <NotificationsIcon fontSize="small" />
          </IconButton>

          <ThemeToggle size="small" />

          <IconButton
            size="small"
            sx={{
              p: 0.5,
              color: (theme) => theme.palette.text.secondary,
              "&:hover": {
                backgroundColor: (theme) => theme.palette.action.hover,
                color: (theme) => theme.palette.text.primary,
              },
            }}
          >
            <SettingsIcon fontSize="small" />
          </IconButton>

          <IconButton
            size="small"
            sx={{
              p: 0.5,
              color: (theme) => theme.palette.text.secondary,
              "&:hover": {
                backgroundColor: (theme) => theme.palette.action.hover,
                color: (theme) => theme.palette.text.primary,
              },
            }}
          >
            <HelpIcon fontSize="small" />
          </IconButton>

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
          <IconButton
            size="small"
            onClick={handleMinimize}
            sx={{
              p: 0.5,
              color: (theme) => theme.palette.text.secondary,
              "&:hover": {
                backgroundColor: (theme) => theme.palette.action.hover,
                color: (theme) => theme.palette.text.primary,
              },
            }}
          >
            <Minimize fontSize="small" />
          </IconButton>

          <IconButton
            size="small"
            onClick={handleMaximize}
            sx={{
              p: 0.5,
              color: (theme) => theme.palette.text.secondary,
              "&:hover": {
                backgroundColor: (theme) => theme.palette.action.hover,
                color: (theme) => theme.palette.text.primary,
              },
            }}
          >
            <CropSquare fontSize="small" />
          </IconButton>

          <IconButton
            size="small"
            onClick={handleClose}
            sx={{
              p: 0.5,
              color: (theme) => theme.palette.text.secondary,
              "&:hover": {
                backgroundColor: alpha("#f44336", 0.8),
                color: "white",
              },
            }}
          >
            <Close fontSize="small" />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
};
