/**
 * 🎯 BottomMenu Component - Universal Camera Viewer
 * Barra inferior fija para acciones rápidas y estado
 */

import React from "react";
import {
  Box,
  Typography,
  IconButton,
  Tooltip,
  Chip,
  useTheme as useMuiTheme,
  alpha,
} from "@mui/material";
import {
  Api as ApiIcon,
  LinkOff as LinkOffIcon,
  Schedule as ScheduleIcon,
  BugReport as BugReportIcon,
  Copyright as CopyrightIcon,
} from "@mui/icons-material";
import { useTheme } from "../../hooks/useTheme";
import { colorTokens } from "../../design-system/tokens";
import { useCameraStoreV2 } from "../../stores/cameraStore.v2";
import { APP_CONFIG, getAppVersion } from "../../config/appConfig";

interface BottomMenuProps {
  sidebarCollapsed?: boolean;
}

export const BottomMenu: React.FC<BottomMenuProps> = ({
  sidebarCollapsed = false,
}) => {
  const muiTheme = useMuiTheme();
  const { effectiveTheme } = useTheme();
  const { getCameraStats } = useCameraStoreV2();
  
  const stats = getCameraStats();
  const [backendConnected] = React.useState(true);
  const [showClock, setShowClock] = React.useState(true);

  // Obtener hora actual
  const [currentTime, setCurrentTime] = React.useState(new Date());
  React.useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const timeString = currentTime.toLocaleTimeString('es-ES', { 
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit'
  });

  // Calcular margen izquierdo basado en el estado del sidebar
  const sidebarWidth = sidebarCollapsed ? 48 : 240;

  return (
    <Box
      sx={{
        position: "fixed",
        bottom: 0,
        left: 0,
        right: 0,
        height: "32px", // Misma altura que el TopBar
        backgroundColor:
          effectiveTheme === "dark"
            ? colorTokens.background.darkPaper // Mismo nivel que el Sidebar
            : colorTokens.background.lightSidebar, // Mismo nivel que el Sidebar
        borderTop: `1px solid ${
          effectiveTheme === "dark"
            ? colorTokens.neutral[700] // Mismo borde que el Sidebar
            : colorTokens.neutral[300] // Mismo borde que el Sidebar
        }`,
        display: "flex",
        alignItems: "center",
        px: 1,
        gap: 2,
        zIndex: muiTheme.zIndex.drawer - 1,
        transition: "all 0.2s ease",
        marginLeft: {
          xs: 0,
          md: `${sidebarWidth}px`,
        },
      }}
    >
      {/* Sección izquierda - Estado del sistema */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, flex: "0 0 auto" }}>
        {/* Estado de conexión backend */}
        <Tooltip title={backendConnected ? "Backend conectado" : "Backend desconectado"}>
          <Box sx={{ display: "flex", alignItems: "center" }}>
            {backendConnected ? (
              <ApiIcon sx={{ fontSize: 16, color: colorTokens.status.connected }} />
            ) : (
              <LinkOffIcon sx={{ fontSize: 16, color: colorTokens.status.error }} />
            )}
          </Box>
        </Tooltip>

        {/* Estado de cámaras */}
        <Tooltip title={`${stats.connected} de ${stats.total} cámaras conectadas`}>
          <Chip
            label={`${stats.connected}/${stats.total}`}
            size="small"
            sx={{
              height: "20px",
              fontSize: "11px",
              backgroundColor: alpha(
                stats.connected > 0 ? colorTokens.status.connected : colorTokens.status.disconnected,
                0.15
              ),
              color: stats.connected > 0 ? colorTokens.status.connected : colorTokens.status.disconnected,
              "& .MuiChip-label": {
                px: 0.75,
              },
            }}
          />
        </Tooltip>
      </Box>

      {/* Sección central - Kipustec Copyright */}
      <Box sx={{ 
        flex: 1, 
        display: "flex", 
        alignItems: "center", 
        justifyContent: "center",
        minWidth: 0,
        px: 2,
      }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.75 }}>
          <CopyrightIcon sx={{ fontSize: 12, color: "text.secondary" }} />
          <Typography
            variant="caption"
            sx={{
              fontSize: "11px",
              color: effectiveTheme === "dark" 
                ? colorTokens.neutral[300]
                : colorTokens.neutral[700],
              fontWeight: 600,
              letterSpacing: "0.02em",
              whiteSpace: "nowrap",
            }}
          >
            {APP_CONFIG.legal.copyright}
          </Typography>
          <Typography
            variant="caption"
            sx={{
              fontSize: "10px",
              color: "text.secondary",
              whiteSpace: "nowrap",
            }}
          >
            {getAppVersion()}
          </Typography>
        </Box>
      </Box>

      {/* Sección derecha - Debug y Hora */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, flex: "0 0 auto" }}>
        {/* Modo debug */}
        <Tooltip title="Consola de desarrollo">
          <IconButton
            size="small"
            onClick={() => console.log("Debug info:", { stats, backendConnected, version: getAppVersion(), showClock, appConfig: APP_CONFIG })}
            sx={{
              p: 0.25,
              color: (theme) => theme.palette.text.secondary,
            }}
          >
            <BugReportIcon sx={{ fontSize: 16 }} />
          </IconButton>
        </Tooltip>

        {/* Reloj toggleable */}
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
          <Tooltip title={showClock ? "Ocultar reloj" : "Mostrar reloj"}>
            <IconButton
              size="small"
              onClick={() => setShowClock(!showClock)}
              sx={{
                p: 0.25,
                color: (theme) => theme.palette.text.secondary,
              }}
            >
              <ScheduleIcon sx={{ fontSize: 16 }} />
            </IconButton>
          </Tooltip>
          {showClock && (
            <Typography
              variant="caption"
              sx={{
                fontSize: "12px",
                fontFamily: "monospace",
                color: "text.secondary",
                minWidth: "65px",
              }}
            >
              {timeString}
            </Typography>
          )}
        </Box>
      </Box>
    </Box>
  );
};