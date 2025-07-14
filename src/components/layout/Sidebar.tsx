/**
 * 🎯 Sidebar Component - Universal Camera Viewer
 * Sidebar lateral izquierdo similar a VS Code
 */

import React from "react";
import {
  Box,
  IconButton,
  Tooltip,
  useTheme as useMuiTheme,
  alpha,
} from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Videocam as CamerasIcon,
  Search as ScannerIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  PlayArrow as StreamingIcon,
  Dashboard as DashboardIcon,
} from "@mui/icons-material";
import { useTheme } from "../../hooks/useTheme";
import { colorTokens } from "../../design-system/tokens";

interface SidebarProps {
  collapsed?: boolean;
  onToggle?: () => void;
}

interface NavItem {
  id: string;
  path: string;
  icon: React.ReactNode;
  label: string;
  tooltip: string;
}

const navItems: NavItem[] = [
  {
    id: "cameras",
    path: "/cameras",
    icon: <CamerasIcon />,
    label: "Cámaras",
    tooltip: "Gestión de Cámaras",
  },
  {
    id: "scanner",
    path: "/scanner",
    icon: <ScannerIcon />,
    label: "Escáner",
    tooltip: "Descubrimiento de Red",
  },
  {
    id: "streaming",
    path: "/streaming",
    icon: <StreamingIcon />,
    label: "Streaming",
    tooltip: "Transmisión en Vivo",
  },
  {
    id: "analytics",
    path: "/analytics",
    icon: <AnalyticsIcon />,
    label: "Analytics",
    tooltip: "Métricas y Análisis",
  },
  {
    id: "settings",
    path: "/settings",
    icon: <SettingsIcon />,
    label: "Configuración",
    tooltip: "Configuración del Sistema",
  },
];

export const Sidebar: React.FC<SidebarProps> = ({
  collapsed = false,
  onToggle,
}) => {
  const muiTheme = useMuiTheme();
  const { effectiveTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  const isActive = (path: string) => {
    return (
      location.pathname === path || location.pathname.startsWith(`${path}/`)
    );
  };

  return (
    <Box
      sx={{
        width: collapsed ? "48px" : "240px",
        height: "100vh",
        backgroundColor:
          effectiveTheme === "dark"
            ? colorTokens.background.darkPaper // Nivel 2: Intermedio
            : colorTokens.background.lightSidebar, // Nivel 2: Intermedio
        borderRight: `1px solid ${
          effectiveTheme === "dark"
            ? colorTokens.background.dark // Separador con nivel 3
            : colorTokens.background.light // Separador con nivel 3
        }`,
        display: "flex",
        flexDirection: "column",
        transition: "width 0.2s ease",
        position: "fixed",
        left: 0,
        top: "32px", // Altura del TopBar
        zIndex: muiTheme.zIndex.drawer,
        overflow: "hidden",
      }}
    >
      {/* Sección de navegación principal */}
      <Box sx={{ flex: 1, pt: 1 }}>
        {navItems.map((item) => {
          const active = isActive(item.path);

          return (
            <Tooltip
              key={item.id}
              title={collapsed ? item.tooltip : ""}
              placement="right"
              arrow
            >
              <Box
                sx={{
                  position: "relative",
                  mb: 0.5,
                  mx: collapsed ? 0.5 : 1,
                }}
              >
                {/* Indicador de estado activo */}
                {active && (
                  <Box
                    sx={{
                      position: "absolute",
                      left: collapsed ? -4 : -8,
                      top: 0,
                      bottom: 0,
                      width: 3,
                      backgroundColor: colorTokens.primary[500],
                      borderRadius: "0 2px 2px 0",
                      zIndex: 1,
                    }}
                  />
                )}

                <IconButton
                  onClick={() => handleNavigation(item.path)}
                  sx={{
                    width: collapsed ? "40px" : "100%",
                    height: "40px",
                    borderRadius: collapsed ? "4px" : "6px",
                    backgroundColor: active
                      ? alpha(colorTokens.primary[500], 0.1)
                      : "transparent",
                    color: active
                      ? colorTokens.primary[
                          effectiveTheme === "dark" ? 400 : 600
                        ]
                      : effectiveTheme === "dark"
                      ? colorTokens.neutral[300]
                      : colorTokens.neutral[600],
                    justifyContent: collapsed ? "center" : "flex-start",
                    px: collapsed ? 0 : 1.5,
                    gap: collapsed ? 0 : 1.5,
                    fontSize: collapsed ? "20px" : "14px",
                    "&:hover": {
                      backgroundColor: active
                        ? alpha(colorTokens.primary[500], 0.15)
                        : alpha(
                            effectiveTheme === "dark"
                              ? colorTokens.neutral[100]
                              : colorTokens.neutral[900],
                            0.05
                          ),
                      color: active
                        ? colorTokens.primary[
                            effectiveTheme === "dark" ? 300 : 700
                          ]
                        : (theme) => theme.palette.text.primary,
                    },
                    transition: "all 0.2s ease",
                  }}
                >
                  {/* Icono */}
                  <Box
                    component="span"
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "18px",
                      minWidth: "20px",
                    }}
                  >
                    {item.icon}
                  </Box>

                  {/* Label (solo cuando no está colapsado) */}
                  {!collapsed && (
                    <Box
                      component="span"
                      sx={{
                        fontSize: "13px",
                        fontWeight: active ? 500 : 400,
                        textTransform: "none",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        flex: 1,
                        textAlign: "left",
                      }}
                    >
                      {item.label}
                    </Box>
                  )}
                </IconButton>
              </Box>
            </Tooltip>
          );
        })}
      </Box>

      {/* Sección inferior - Controles adicionales */}
      <Box
        sx={{
          borderTop: `1px solid ${
            effectiveTheme === "dark"
              ? colorTokens.neutral[700]
              : colorTokens.neutral[300]
          }`,
          p: 1,
          display: "flex",
          flexDirection: "column",
          gap: 0.5,
        }}
      >
        {/* Botón de colapsar/expandir */}
        <Tooltip
          title={collapsed ? "Expandir Panel" : "Colapsar Panel"}
          placement="right"
          arrow
        >
          <IconButton
            onClick={onToggle}
            sx={{
              width: collapsed ? "40px" : "100%",
              height: "32px",
              borderRadius: "4px",
              color:
                effectiveTheme === "dark"
                  ? colorTokens.neutral[400]
                  : colorTokens.neutral[600],
              fontSize: "16px",
              "&:hover": {
                backgroundColor: alpha(
                  effectiveTheme === "dark"
                    ? colorTokens.neutral[100]
                    : colorTokens.neutral[900],
                  0.05
                ),
                color: (theme) => theme.palette.text.primary,
              },
            }}
          >
            <Box
              sx={{
                transform: collapsed ? "rotate(0deg)" : "rotate(180deg)",
                transition: "transform 0.2s ease",
              }}
            >
              ⮜
            </Box>
            {!collapsed && (
              <Box
                component="span"
                sx={{
                  ml: 1,
                  fontSize: "12px",
                  fontWeight: 400,
                }}
              >
                Colapsar
              </Box>
            )}
          </IconButton>
        </Tooltip>

        {/* Información de estado */}
        {!collapsed && (
          <Box
            sx={{
              px: 1,
              py: 0.5,
              fontSize: "10px",
              color:
                effectiveTheme === "dark"
                  ? colorTokens.neutral[500]
                  : colorTokens.neutral[600],
              textAlign: "center",
              borderRadius: "4px",
              backgroundColor: alpha(
                effectiveTheme === "dark"
                  ? colorTokens.neutral[600]
                  : colorTokens.neutral[400],
                0.1
              ),
            }}
          >
            v2.0.0
          </Box>
        )}
      </Box>
    </Box>
  );
};
