/**
 * 🎯 Scan Results Component - Universal Camera Viewer
 * Muestra los resultados del escaneo de red
 * Optimizado con virtualización para listas grandes
 */

import React, { useState, useCallback, useMemo, memo } from "react";
import { FixedSizeList as List } from "react-window";
import {
  Box,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
  Paper,
  Collapse,
  alpha,
  Fade,
  Zoom,
  keyframes,
} from "@mui/material";
import {
  Videocam as CameraIcon,
  Computer as DeviceIcon,
  Router as RouterIcon,
  Smartphone as MobileIcon,
  CheckCircle as SelectedIcon,
  RadioButtonUnchecked as UnselectedIcon,
  Info as InfoIcon,
  ContentCopy as CopyIcon,
  ExpandMore,
  ExpandLess,
} from "@mui/icons-material";
import { colorTokens, borderTokens } from "../../../design-system/tokens";

// Animación de pulso para dispositivos escaneando
const pulseAnimation = keyframes`
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
  100% {
    opacity: 1;
  }
`;

// Animación de entrada
const slideIn = keyframes`
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
`;

// Animación de fade in up para detalles expandibles
const fadeInUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

export interface ScanResult {
  ip: string;
  mac?: string;
  hostname?: string;
  deviceType: "camera" | "router" | "computer" | "mobile" | "unknown";
  probability: number; // 0-1 probabilidad de ser cámara
  openPorts: number[];
  manufacturer?: string;
  model?: string;
  status: "scanning" | "completed" | "error";
}

interface ScanResultsProps {
  results: ScanResult[];
  onSelectIP: (ip: string) => void;
  selectedIP?: string;
}

// Componente de ítem memoizado para rendimiento
interface ResultItemProps {
  index: number;
  style: React.CSSProperties;
  data: {
    results: ScanResult[];
    selectedIP?: string;
    expandedIP: string | null;
    onSelectIP: (ip: string) => void;
    handleCopyIP: (e: React.MouseEvent, ip: string) => void;
    handleToggleExpand: (ip: string) => void;
  };
}

const ResultItem = memo<ResultItemProps>(({ index, style, data }) => {
  const { results, selectedIP, expandedIP, onSelectIP, handleCopyIP, handleToggleExpand } = data;
  const result = results[index];
  const isSelected = selectedIP === result.ip;
  const isExpanded = expandedIP === result.ip;
  const isProbableCamera = result.probability >= 0.7;

  const getDeviceIcon = (deviceType: ScanResult["deviceType"]) => {
    switch (deviceType) {
      case "camera":
        return <CameraIcon />;
      case "router":
        return <RouterIcon />;
      case "computer":
        return <DeviceIcon />;
      case "mobile":
        return <MobileIcon />;
      default:
        return <DeviceIcon />;
    }
  };

  const getProbabilityColor = (probability: number) => {
    if (probability >= 0.8) return colorTokens.status.connected;
    if (probability >= 0.5) return colorTokens.status.connecting;
    return colorTokens.neutral[500];
  };

  const getProbabilityLabel = (probability: number) => {
    if (probability >= 0.8) return "Alta";
    if (probability >= 0.5) return "Media";
    return "Baja";
  };

  return (
    <div style={style}>
      <Fade
        in
        timeout={300 + index * 50}
        style={{ transitionDelay: `${Math.min(index * 50, 500)}ms` }}
      >
        <React.Fragment>
          <ListItem
            disablePadding
            sx={{
              mb: 0.5,
              backgroundColor: isSelected
                ? alpha(colorTokens.primary[500], 0.08)
                : "transparent",
              borderRadius: borderTokens.radius.md,
              border: isSelected
                ? `1px solid ${alpha(colorTokens.primary[500], 0.3)}`
                : "1px solid transparent",
              transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
              animation: result.status === "scanning" 
                ? `${pulseAnimation} 2s ease-in-out infinite`
                : `${slideIn} 0.4s ease-out`,
              "&:hover": {
                borderColor: alpha(colorTokens.primary[500], 0.2),
                transform: "translateX(4px)",
              },
            }}
          >
            <ListItemButton
              onClick={() => {
                onSelectIP(result.ip);
                handleToggleExpand(result.ip);
              }}
              sx={{
                borderRadius: 1,
                py: 1,
                "&:hover": {
                  backgroundColor: (theme) =>
                    alpha(
                      theme.palette.mode === "dark"
                        ? colorTokens.neutral[100]
                        : colorTokens.neutral[900],
                      0.04
                    ),
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>
                {isSelected ? (
                  <SelectedIcon
                    sx={{
                      color: colorTokens.primary[500],
                      fontSize: 20,
                    }}
                  />
                ) : (
                  <UnselectedIcon
                    sx={{
                      color: "text.disabled",
                      fontSize: 20,
                    }}
                  />
                )}
              </ListItemIcon>

              <ListItemIcon sx={{ minWidth: 40 }}>
                <Tooltip 
                  title={`Tipo: ${result.deviceType}`} 
                  placement="top"
                  arrow
                >
                  <Box
                    sx={{
                      color: isProbableCamera
                        ? colorTokens.status.connected
                        : "text.secondary",
                      display: "flex",
                      alignItems: "center",
                      transition: "transform 0.3s ease",
                      "& svg": {
                        fontSize: 24,
                      },
                    }}
                  >
                    {getDeviceIcon(result.deviceType)}
                  </Box>
                </Tooltip>
              </ListItemIcon>

              <ListItemText
                primary={
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Typography
                      variant="body2"
                      sx={{
                        fontFamily: "monospace",
                        fontWeight: isSelected ? 600 : 400,
                      }}
                    >
                      {result.ip}
                    </Typography>
                    {result.hostname && (
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                          maxWidth: 120,
                        }}
                      >
                        ({result.hostname})
                      </Typography>
                    )}
                  </Box>
                }
                secondary={
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.5 }}>
                    {/* Probabilidad de ser cámara */}
                    {isProbableCamera && (
                      <Chip
                        label={`${Math.round(result.probability * 100)}% cámara`}
                        size="small"
                        sx={{
                          height: 18,
                          fontSize: "0.65rem",
                          backgroundColor: alpha(
                            getProbabilityColor(result.probability),
                            0.15
                          ),
                          color: getProbabilityColor(result.probability),
                          fontWeight: 500,
                        }}
                      />
                    )}

                    {/* Puertos abiertos */}
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ fontSize: "0.7rem" }}
                    >
                      {result.openPorts.length} puerto(s)
                    </Typography>

                    {/* Fabricante si está disponible */}
                    {result.manufacturer && (
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ fontSize: "0.7rem" }}
                      >
                        • {result.manufacturer}
                      </Typography>
                    )}
                  </Box>
                }
              />

              <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                {/* Estado del escaneo */}
                {result.status === "scanning" && (
                  <Box sx={{ width: 20, height: 20 }}>
                    <LinearProgress
                      sx={{
                        borderRadius: 10,
                        height: 3,
                      }}
                    />
                  </Box>
                )}

                {/* Botón de copiar IP */}
                <Tooltip title="Copiar IP">
                  <IconButton
                    size="small"
                    onClick={(e) => handleCopyIP(e, result.ip)}
                    sx={{
                      opacity: 0.7,
                      "&:hover": { opacity: 1 },
                    }}
                  >
                    <CopyIcon fontSize="small" />
                  </IconButton>
                </Tooltip>

                {/* Botón expandir/colapsar */}
                <IconButton size="small">
                  {isExpanded ? <ExpandLess /> : <ExpandMore />}
                </IconButton>
              </Box>
            </ListItemButton>
          </ListItem>

          {/* Detalles expandibles - fuera de virtualización para simplicidad */}
          {isExpanded && (
            <Collapse in={isExpanded} timeout="auto">
              <Box sx={{ pl: 7, pr: 2, pb: 2 }}>
                <Paper
                  variant="outlined"
                  sx={{
                    p: 1.5,
                    backgroundColor: (theme) =>
                      theme.palette.mode === "dark"
                        ? "rgba(255, 255, 255, 0.02)"
                        : "rgba(0, 0, 0, 0.01)",
                    borderRadius: borderTokens.radius.md,
                    animation: `${fadeInUp} 0.3s ease-out`,
                  }}
                >
                  <Box
                    sx={{
                      display: "grid",
                      gridTemplateColumns: "auto 1fr",
                      gap: 1,
                      alignItems: "start",
                    }}
                  >
                    {result.mac && (
                      <>
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          sx={{ fontWeight: 500 }}
                        >
                          MAC:
                        </Typography>
                        <Typography
                          variant="caption"
                          sx={{ fontFamily: "monospace" }}
                        >
                          {result.mac}
                        </Typography>
                      </>
                    )}

                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ fontWeight: 500 }}
                    >
                      Puertos:
                    </Typography>
                    <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
                      {result.openPorts.map((port, idx) => (
                        <Zoom 
                          key={port} 
                          in 
                          timeout={200 + idx * 50}
                          style={{ transitionDelay: `${idx * 50}ms` }}
                        >
                          <Chip
                            label={port}
                            size="small"
                            sx={{
                              height: 18,
                              fontSize: "0.65rem",
                              fontFamily: "monospace",
                              transition: "all 0.3s ease",
                              "&:hover": {
                                backgroundColor: alpha(colorTokens.primary[500], 0.1),
                                transform: "scale(1.1)",
                              },
                            }}
                          />
                        </Zoom>
                      ))}
                    </Box>

                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ fontWeight: 500 }}
                    >
                      Probabilidad:
                    </Typography>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <LinearProgress
                        variant="determinate"
                        value={result.probability * 100}
                        sx={{
                          width: 80,
                          height: 6,
                          borderRadius: 3,
                          backgroundColor: (theme) =>
                            alpha(getProbabilityColor(result.probability), 0.2),
                          "& .MuiLinearProgress-bar": {
                            borderRadius: 3,
                            backgroundColor: getProbabilityColor(result.probability),
                          },
                        }}
                      />
                      <Typography variant="caption">
                        {getProbabilityLabel(result.probability)}
                      </Typography>
                    </Box>

                    {result.model && (
                      <>
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          sx={{ fontWeight: 500 }}
                        >
                          Modelo:
                        </Typography>
                        <Typography variant="caption">{result.model}</Typography>
                      </>
                    )}
                  </Box>
                </Paper>
              </Box>
            </Collapse>
          )}
        </React.Fragment>
      </Fade>
    </div>
  );
});

ResultItem.displayName = 'ResultItem';

export const ScanResults = memo<ScanResultsProps>(({
  results,
  onSelectIP,
  selectedIP,
}) => {
  const [expandedIP, setExpandedIP] = useState<string | null>(null);

  // Ordenar resultados con memoización
  const sortedResults = useMemo(() => {
    return [...results].sort((a, b) => {
      // Primero por probabilidad de ser cámara
      if (b.probability !== a.probability) {
        return b.probability - a.probability;
      }
      // Luego por cantidad de puertos abiertos
      return b.openPorts.length - a.openPorts.length;
    });
  }, [results]);

  // Handlers memoizados
  const handleCopyIP = useCallback((e: React.MouseEvent, ip: string) => {
    e.stopPropagation();
    navigator.clipboard.writeText(ip);
  }, []);

  const handleToggleExpand = useCallback((ip: string) => {
    setExpandedIP((prev) => prev === ip ? null : ip);
  }, []);

  // Datos para el componente virtualizado
  const itemData = useMemo(() => ({
    results: sortedResults,
    selectedIP,
    expandedIP,
    onSelectIP,
    handleCopyIP,
    handleToggleExpand,
  }), [sortedResults, selectedIP, expandedIP, onSelectIP, handleCopyIP, handleToggleExpand]);

  if (results.length === 0) {
    return (
      <Fade in timeout={600}>
        <Box
          sx={{
            p: 3,
            textAlign: "center",
            color: "text.secondary",
          }}
        >
          <DeviceIcon sx={{ fontSize: 48, opacity: 0.3, mb: 1 }} />
          <Typography variant="body2">
            No se han encontrado dispositivos aún
          </Typography>
          <Typography variant="caption">
            Inicia un escaneo para buscar cámaras en tu red
          </Typography>
        </Box>
      </Fade>
    );
  }

  // Usar lista virtualizada para rendimiento con muchos resultados
  if (sortedResults.length > 20) {
    return (
      <Box sx={{ height: "100%", width: "100%" }}>
        <List
          height={400} // Altura del contenedor
          itemCount={sortedResults.length}
          itemSize={85} // Altura estimada de cada ítem
          width="100%"
          itemData={itemData}
        >
          {ResultItem}
        </List>
      </Box>
    );
  }

  // Para listas pequeñas, renderizar normalmente
  return (
    <Box sx={{ p: 0 }}>
      {sortedResults.map((_, index) => (
        <ResultItem
          key={sortedResults[index].ip}
          index={index}
          style={{}}
          data={itemData}
        />
      ))}
    </Box>
  );
});

// Añadir displayName para debugging
ScanResults.displayName = 'ScanResults';