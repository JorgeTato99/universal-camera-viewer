/**
 * 🎯 Sidebar Component - Universal Camera Viewer
 * Sidebar lateral izquierdo similar a VS Code
 */

import React, { useState } from "react";
import {
  Box,
  IconButton,
  Tooltip,
  useTheme as useMuiTheme,
  alpha,
  Collapse,
} from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Videocam as CamerasIcon,
  Search as ScannerIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  ExpandMore as ExpandMoreIcon,
  Visibility as ViewIcon,
  Assignment as RegisterIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  NetworkCheck as NetworkIcon,
  PortableWifiOff as PortIcon,
  VpnKey as AccessIcon,
  Dashboard as DashboardIcon,
  Timeline as TimelineIcon,
  Event as EventIcon,
  Speed as PerformanceIcon,
  Description as ReportIcon,
  CloudUpload as PublishingIcon,
  PlayCircle as PlayCircleIcon,
  History as HistoryIcon,
  Route as RouteIcon,
} from "@mui/icons-material";
import { useTheme } from "../../hooks/useTheme";
import { colorTokens } from "../../design-system/tokens";

interface SidebarProps {
  collapsed?: boolean;
  onToggle?: () => void;
}

interface SubItem {
  id: string;
  path: string;
  icon: React.ReactNode;
  label: string;
  tooltip: string;
}

interface NavItem {
  id: string;
  path?: string;
  icon: React.ReactNode;
  label: string;
  tooltip: string;
  subItems?: SubItem[];
}

const navItems: NavItem[] = [
  {
    id: "cameras",
    icon: <CamerasIcon />,
    label: "Cámaras",
    tooltip: "Gestión de Cámaras",
    subItems: [
      {
        id: "cameras-live",
        path: "/cameras/live",
        icon: <ViewIcon />,
        label: "Vista en Vivo",
        tooltip: "Ver cámaras en tiempo real",
      },
      {
        id: "cameras-register",
        path: "/cameras/register",
        icon: <RegisterIcon />,
        label: "Registro",
        tooltip: "Gestionar cámaras registradas",
      },
    ],
  },
  {
    id: "scanner",
    path: "/scanner",
    icon: <ScannerIcon />,
    label: "Escáner",
    tooltip: "Centro de Escaneo",
    subItems: [
      {
        id: "scanner-network",
        path: "/scanner/network",
        icon: <NetworkIcon />,
        label: "Escaneo de Red",
        tooltip: "Descubrir dispositivos en la red",
      },
      {
        id: "scanner-ports",
        path: "/scanner/ports",
        icon: <PortIcon />,
        label: "Escaneo de Puertos",
        tooltip: "Analizar puertos abiertos",
      },
      {
        id: "scanner-access",
        path: "/scanner/access",
        icon: <AccessIcon />,
        label: "Prueba de Acceso",
        tooltip: "Verificar credenciales",
      },
    ],
  },
  {
    id: "statistics",
    path: "/statistics",
    icon: <AnalyticsIcon />,
    label: "Estadísticas",
    tooltip: "Métricas y Análisis",
    subItems: [
      {
        id: "statistics-overview",
        path: "/statistics/overview",
        icon: <DashboardIcon />,
        label: "General",
        tooltip: "Resumen general del sistema",
      },
      {
        id: "statistics-connections",
        path: "/statistics/connections",
        icon: <TimelineIcon />,
        label: "Conexiones",
        tooltip: "Análisis de conexiones",
      },
      {
        id: "statistics-events",
        path: "/statistics/events",
        icon: <EventIcon />,
        label: "Eventos",
        tooltip: "Línea de tiempo de eventos",
      },
      {
        id: "statistics-performance",
        path: "/statistics/performance",
        icon: <PerformanceIcon />,
        label: "Rendimiento",
        tooltip: "Métricas de rendimiento",
      },
      {
        id: "statistics-network",
        path: "/statistics/network",
        icon: <NetworkIcon />,
        label: "Red",
        tooltip: "Historial de escaneos de red",
      },
      {
        id: "statistics-reports",
        path: "/statistics/reports",
        icon: <ReportIcon />,
        label: "Reportes",
        tooltip: "Reportes detallados",
      },
    ],
  },
  {
    id: "publishing",
    icon: <PublishingIcon />,
    label: "Publicación",
    tooltip: "Gestión MediaMTX",
    subItems: [
      {
        id: "publishing-dashboard",
        path: "/publishing/dashboard",
        icon: <DashboardIcon />,
        label: "Dashboard",
        tooltip: "Panel de control MediaMTX",
      },
      {
        id: "publishing-active",
        path: "/publishing/active",
        icon: <PlayCircleIcon />,
        label: "Publicaciones",
        tooltip: "Control de publicaciones activas",
      },
      {
        id: "publishing-metrics",
        path: "/publishing/metrics",
        icon: <AnalyticsIcon />,
        label: "Métricas",
        tooltip: "Estadísticas de streaming",
      },
      {
        id: "publishing-history",
        path: "/publishing/history",
        icon: <HistoryIcon />,
        label: "Historial",
        tooltip: "Registro de sesiones",
      },
      {
        id: "publishing-paths",
        path: "/publishing/paths",
        icon: <RouteIcon />,
        label: "Configuración",
        tooltip: "Gestión de paths MediaMTX",
      },
    ],
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
  const [expandedItems, setExpandedItems] = useState<string[]>(() => {
    // Auto-expandir el item activo
    const path = location.pathname;
    if (path.startsWith("/cameras")) return ["cameras"];
    if (path.startsWith("/scanner")) return ["scanner"];
    if (path.startsWith("/statistics")) return ["statistics"];
    if (path.startsWith("/publishing")) return ["publishing"];
    return ["cameras"];
  });

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  const isActive = (path?: string) => {
    if (!path) return false;
    return (
      location.pathname === path || location.pathname.startsWith(`${path}/`)
    );
  };

  const isParentActive = (subItems?: SubItem[]) => {
    if (!subItems) return false;
    return subItems.some(subItem => isActive(subItem.path));
  };

  const toggleExpanded = (itemId: string) => {
    setExpandedItems(prev =>
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  return (
    <Box
      sx={{
        width: collapsed ? "48px" : "240px",
        height: "calc(100vh - 32px)", // Resta la altura del TopBar
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
      <Box sx={{ flex: 1, pt: 1, overflowY: "auto", overflowX: "hidden" }}>
        {navItems.map((item) => {
          const hasSubItems = item.subItems && item.subItems.length > 0;
          const isExpanded = expandedItems.includes(item.id);
          const active = item.path ? isActive(item.path) : isParentActive(item.subItems);

          return (
            <Box key={item.id}>
              <Tooltip
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
                    onClick={() => {
                      if (item.path) {
                        handleNavigation(item.path);
                      }
                      if (hasSubItems) {
                        toggleExpanded(item.id);
                      }
                    }}
                    sx={{
                      width: collapsed ? "44px" : "100%",
                      height: "44px",
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
                        fontSize: "20px",
                        minWidth: "22px",
                      }}
                    >
                      {item.icon}
                    </Box>

                    {/* Label (solo cuando no está colapsado) */}
                    {!collapsed && (
                      <Box
                        component="span"
                        sx={{
                          fontSize: "14px",
                          fontWeight: active ? 600 : 400,
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

                    {/* Indicador de expansión para items con subopciones */}
                    {!collapsed && hasSubItems && (
                      <Box
                        component="span"
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: "16px",
                          transition: "transform 0.2s ease",
                          transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)",
                        }}
                      >
                        <ExpandMoreIcon fontSize="small" />
                      </Box>
                    )}
                  </IconButton>
                </Box>
              </Tooltip>

              {/* Subitems */}
              {!collapsed && hasSubItems && (
                <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                  <Box sx={{ ml: 2.5, mt: 0.25 }}>
                    {item.subItems?.map((subItem) => {
                      const subActive = isActive(subItem.path);

                      return (
                        <Tooltip
                          key={subItem.id}
                          title=""
                          placement="right"
                          arrow
                        >
                          <Box
                            sx={{
                              position: "relative",
                              mb: 0.5,
                              mx: 1,
                            }}
                          >
                            <IconButton
                              onClick={() => handleNavigation(subItem.path)}
                              sx={{
                                width: "100%",
                                height: "32px",
                                borderRadius: "4px",
                                backgroundColor: subActive
                                  ? alpha(colorTokens.primary[500], 0.06)
                                  : "transparent",
                                color: subActive
                                  ? colorTokens.primary[
                                      effectiveTheme === "dark" ? 400 : 600
                                    ]
                                  : effectiveTheme === "dark"
                                  ? colorTokens.neutral[500]
                                  : colorTokens.neutral[600],
                                justifyContent: "flex-start",
                                px: 1.25,
                                gap: 1.25,
                                fontSize: "12px",
                                "&:hover": {
                                  backgroundColor: subActive
                                    ? alpha(colorTokens.primary[500], 0.12)
                                    : alpha(
                                        effectiveTheme === "dark"
                                          ? colorTokens.neutral[100]
                                          : colorTokens.neutral[900],
                                        0.04
                                      ),
                                  color: subActive
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
                                  fontSize: "14px",
                                  minWidth: "16px",
                                }}
                              >
                                {subItem.icon}
                              </Box>

                              {/* Label */}
                              <Box
                                component="span"
                                sx={{
                                  fontSize: "12px",
                                  fontWeight: subActive ? 500 : 400,
                                  textTransform: "none",
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  whiteSpace: "nowrap",
                                  flex: 1,
                                  textAlign: "left",
                                }}
                              >
                                {subItem.label}
                              </Box>
                            </IconButton>
                          </Box>
                        </Tooltip>
                      );
                    })}
                  </Box>
                </Collapse>
              )}
            </Box>
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
          px: 0.75,
          py: 0.5,
          display: "flex",
          flexDirection: "column",
          gap: 0,
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
              width: collapsed ? "32px" : "100%",
              height: "24px",
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
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {collapsed ? <ChevronRightIcon fontSize="small" /> : <ChevronLeftIcon fontSize="small" />}
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

      </Box>
    </Box>
  );
};
