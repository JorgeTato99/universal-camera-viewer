/**
 * 🔍 Port Scan Page - Universal Camera Viewer
 * Página dedicada al escaneo de puertos en dispositivos específicos
 * Optimizada con memo y manejo de estado eficiente
 */

import React, { useState, useCallback, useEffect, useMemo, memo } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  Fade,
  useTheme,
  Container,
  Breadcrumbs,
  Link,
  Chip,
  Alert,
  AlertTitle,
  TextField,
  InputAdornment,
} from "@mui/material";
import {
  PortableWifiOff as PortIcon,
  NavigateNext as NavigateNextIcon,
  ArrowBack as BackIcon,
  VpnKey as AccessIcon,
} from "@mui/icons-material";
import { useNavigate, useSearchParams } from "react-router-dom";
import { colorTokens, spacingTokens, borderTokens } from "../../../../design-system/tokens";
import { PortScanPanel } from "../../components/PortScanPanel";
import { useScannerStore } from "../../../../stores/scannerStore";

const PortScanPage = memo(() => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  // Obtener IP de los parámetros de URL o del store
  const ipFromUrl = searchParams.get('ip');
  const selectedDevice = useScannerStore((state) => state.selectedDevice);
  const targetIP = ipFromUrl || selectedDevice?.ip || "";

  // Estado local
  const [scanComplete, setScanComplete] = useState(false);
  const [discoveredPorts, setDiscoveredPorts] = useState<number[]>([]);
  const [manualIP, setManualIP] = useState("");
  const [ipError, setIpError] = useState("");
  const [useManualIP, setUseManualIP] = useState(!targetIP);

  // Validar formato de IP
  const validateIP = useCallback((ip: string): boolean => {
    if (!ip) return false;
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipRegex.test(ip)) return false;
    
    // Verificar que cada octeto esté entre 0 y 255
    const octets = ip.split('.');
    return octets.every(octet => {
      const num = parseInt(octet, 10);
      return num >= 0 && num <= 255;
    });
  }, []);

  // IP final a usar (manual o de URL/store)
  const finalIP = useManualIP ? manualIP : targetIP;
  const hasValidIP = useMemo(() => validateIP(finalIP), [finalIP, validateIP]);

  // Handlers
  const handleBack = useCallback(() => {
    navigate("/scanner/network");
  }, [navigate]);

  const handleComplete = useCallback((ports: number[]) => {
    setScanComplete(true);
    setDiscoveredPorts(ports);
  }, []);

  const handleAccessTest = useCallback(() => {
    // Navegar a prueba de acceso con IP y puertos
    const portsParam = discoveredPorts.join(',');
    navigate(`/scanner/access?ip=${finalIP}&ports=${portsParam}`);
  }, [finalIP, discoveredPorts, navigate]);

  const handleNewScan = useCallback(() => {
    navigate("/scanner/network");
  }, [navigate]);

  // Manejar cambio de IP manual
  const handleIPChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setManualIP(value);
    if (value && !validateIP(value)) {
      setIpError("Formato de IP inválido (ej: 192.168.1.100)");
    } else {
      setIpError("");
    }
  }, [validateIP]);

  // Alternar entre IP manual y automática
  const handleToggleManualIP = useCallback(() => {
    setUseManualIP(!useManualIP);
    setManualIP("");
    setIpError("");
    setScanComplete(false);
    setDiscoveredPorts([]);
  }, [useManualIP]);

  return (
    <Container maxWidth="xl" sx={{ py: 3, height: "100%", display: "flex", flexDirection: "column" }}>
      {/* Breadcrumbs */}
      <Breadcrumbs 
        separator={<NavigateNextIcon fontSize="small" />}
        sx={{ mb: 2 }}
      >
        <Link
          component="button"
          variant="body2"
          onClick={() => navigate("/scanner")}
          sx={{ 
            textDecoration: "none",
            color: "text.secondary",
            "&:hover": { color: "primary.main" }
          }}
        >
          Escáner
        </Link>
        <Link
          component="button"
          variant="body2"
          onClick={() => navigate("/scanner/network")}
          sx={{ 
            textDecoration: "none",
            color: "text.secondary",
            "&:hover": { color: "primary.main" }
          }}
        >
          Escaneo de Red
        </Link>
        <Typography color="text.primary" variant="body2">
          Escaneo de Puertos
        </Typography>
      </Breadcrumbs>

      {/* Header */}
      <Fade in timeout={600}>
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
            <PortIcon sx={{ fontSize: 32, color: "primary.main" }} />
            <Typography variant="h4" component="h1">
              Escaneo de Puertos
            </Typography>
            {hasValidIP && (
              <Chip 
                label={`IP: ${finalIP}`}
                color="primary"
                variant="outlined"
                sx={{ ml: 2 }}
              />
            )}
          </Box>
          <Typography variant="body1" color="text.secondary">
            Analiza los puertos abiertos en el dispositivo seleccionado para identificar servicios de cámara
          </Typography>
        </Box>
      </Fade>

      {/* Contenido principal */}
      <Box sx={{ flex: 1, display: "flex", flexDirection: "column", gap: 2 }}>
        {/* Opción de entrada manual de IP */}
        {(!targetIP || useManualIP) && (
          <Fade in timeout={600}>
            <Paper
              sx={{
                p: 3,
                mb: 2,
                borderRadius: borderTokens.radius.lg,
                backgroundColor: theme.palette.mode === "dark"
                  ? colorTokens.background.darkElevated
                  : colorTokens.background.lightElevated,
              }}
            >
              <Typography variant="h6" gutterBottom>
                Configuración de IP
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {targetIP 
                  ? "Se detectó una IP del escaneo de red, pero puedes ingresar una IP diferente si lo deseas."
                  : "No se detectó ninguna IP del escaneo de red. Ingresa manualmente la IP del dispositivo a escanear."
                }
              </Typography>
              
              <Box sx={{ display: "flex", gap: 2, alignItems: "flex-start" }}>
                <TextField
                  label="Dirección IP"
                  value={manualIP}
                  onChange={handleIPChange}
                  error={!!ipError}
                  helperText={ipError || "Ejemplo: 192.168.1.100"}
                  placeholder="192.168.1.100"
                  fullWidth
                  sx={{ maxWidth: 300 }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <PortIcon sx={{ fontSize: 20 }} />
                      </InputAdornment>
                    ),
                  }}
                />
                
                {targetIP && (
                  <Button
                    variant="outlined"
                    onClick={handleToggleManualIP}
                    sx={{ minWidth: 150 }}
                  >
                    {useManualIP ? "Usar IP detectada" : "Usar otra IP"}
                  </Button>
                )}
              </Box>
              
              {targetIP && !useManualIP && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  Usando IP detectada: <strong>{targetIP}</strong>
                </Alert>
              )}
            </Paper>
          </Fade>
        )}

        <Paper
          sx={{
            p: 3,
            flex: 1,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            borderRadius: borderTokens.radius.lg,
          }}
        >
          {/* Panel de escaneo de puertos */}
          <Box sx={{ flex: 1 }}>
            {hasValidIP ? (
              <PortScanPanel
                selectedIP={finalIP}
                onComplete={handleComplete}
                onBack={handleBack}
              />
            ) : (
              <Box sx={{ 
                display: "flex", 
                flexDirection: "column", 
                alignItems: "center", 
                justifyContent: "center",
                height: "100%",
                textAlign: "center",
                p: 4
              }}>
                <PortIcon sx={{ fontSize: 64, color: "text.secondary", mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Ingresa una IP válida para comenzar
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Necesitas especificar una dirección IP válida para escanear sus puertos.
                </Typography>
              </Box>
            )}
          </Box>

          {/* Resultados del escaneo */}
          {scanComplete && discoveredPorts.length > 0 && (
            <Fade in timeout={600}>
              <Box 
                sx={{ 
                  mt: 3, 
                  p: 2, 
                  backgroundColor: theme.palette.mode === "dark"
                    ? "rgba(76, 175, 80, 0.1)"
                    : "rgba(76, 175, 80, 0.05)",
                  borderRadius: borderTokens.radius.md,
                  border: `1px solid ${colorTokens.status.connected}`,
                }}
              >
                <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                  Escaneo completado
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Se encontraron {discoveredPorts.length} puerto(s) abiertos que podrían corresponder a servicios de cámara.
                </Typography>
                <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                  {discoveredPorts.map((port) => (
                    <Chip
                      key={port}
                      label={`Puerto ${port}`}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  ))}
                </Box>
              </Box>
            </Fade>
          )}

          {/* Acciones */}
          <Box 
            sx={{ 
              mt: 3, 
              pt: 2, 
              borderTop: `1px solid ${theme.palette.divider}`,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center"
            }}
          >
            <Button
              startIcon={<BackIcon />}
              onClick={handleBack}
              sx={{ textTransform: "none" }}
            >
              Volver al escaneo de red
            </Button>

            <Box sx={{ display: "flex", gap: 2 }}>
              {scanComplete && (
                <Button
                  onClick={handleNewScan}
                  sx={{ textTransform: "none" }}
                >
                  Escanear otro dispositivo
                </Button>
              )}
              
              <Button
                variant="contained"
                startIcon={<AccessIcon />}
                onClick={handleAccessTest}
                disabled={!scanComplete || discoveredPorts.length === 0}
                sx={{ textTransform: "none" }}
              >
                Probar acceso
              </Button>
            </Box>
          </Box>
        </Paper>

        {/* Información adicional */}
        <Paper
          sx={{
            p: 2,
            backgroundColor: theme.palette.mode === "dark"
              ? colorTokens.background.darkElevated
              : colorTokens.background.lightElevated,
            borderRadius: borderTokens.radius.lg,
          }}
        >
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            ℹ️ Información sobre puertos comunes
          </Typography>
          <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1, mt: 1 }}>
            <Typography variant="caption" color="text.secondary">
              • Puerto 80: HTTP/ONVIF (Dahua)
            </Typography>
            <Typography variant="caption" color="text.secondary">
              • Puerto 554: RTSP streaming
            </Typography>
            <Typography variant="caption" color="text.secondary">
              • Puerto 2020: ONVIF (TP-Link)
            </Typography>
            <Typography variant="caption" color="text.secondary">
              • Puerto 8000: ONVIF (Steren)
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
});

// Añadir displayName para debugging
PortScanPage.displayName = 'PortScanPage';

export default PortScanPage;