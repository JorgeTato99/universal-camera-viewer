/**
 * 🌐 Network Scan Page - Universal Camera Viewer
 * Página dedicada al escaneo de red para descubrimiento de dispositivos
 * Optimizada con memo y manejo de estado eficiente
 */

import React, { useState, useCallback, useMemo, memo } from "react";
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
} from "@mui/material";
import {
  NetworkCheck as NetworkIcon,
  NavigateNext as NavigateNextIcon,
  Refresh as RefreshIcon,
} from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import { colorTokens, spacingTokens, borderTokens } from "../../../../design-system/tokens";
import { NetworkScanPanel } from "../../components/NetworkScanPanel";
import { ScanResults } from "../../components/ScanResults";
import { ScanSummary } from "../../components/ScanSummary";
import { useScannerStore } from "../../../../stores/scannerStore";
import { ScanStatus, DeviceScanResult } from "../../../../types/scanner.types";

const NetworkScanPage = memo(() => {
  const theme = useTheme();
  const navigate = useNavigate();
  
  // Estado del store
  const currentScan = useScannerStore((state) => state.currentScan);
  const scanResults = useScannerStore((state) => state.results) || [];
  const selectedDevice = useScannerStore((state) => state.selectedDevice);
  
  // Estados derivados
  const isScanning = currentScan?.status === ScanStatus.SCANNING;
  const scanProgress = currentScan?.progress?.scanned_ips 
    ? Math.round((currentScan.progress.scanned_ips / currentScan.progress.total_ips) * 100)
    : 0;
  
  // Estado local para UI
  const [selectedIP, setSelectedIP] = useState<string>("");

  // Filtrar resultados con alta probabilidad - memoizado
  const possibleCameras = useMemo(
    () => scanResults.filter((r: any) => r.probability > 0.7).length,
    [scanResults]
  );

  // Handlers
  const handleIPSelection = useCallback((ip: string) => {
    setSelectedIP(ip);
    // TODO: Guardar en el store para compartir con otras páginas
    // useScannerStore.getState().selectDevice(device);
  }, []);

  const handlePortScanNavigation = useCallback(() => {
    if (selectedIP) {
      // Navegar a escaneo de puertos con la IP seleccionada
      navigate(`/scanner/ports?ip=${selectedIP}`);
    }
  }, [selectedIP, navigate]);

  const handleRefresh = useCallback(() => {
    // TODO: Implementar lógica de refresco
    console.log("Refrescar escaneo de red");
  }, []);

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
        <Typography color="text.primary" variant="body2">
          Escaneo de Red
        </Typography>
      </Breadcrumbs>

      {/* Header */}
      <Fade in timeout={600}>
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
            <NetworkIcon sx={{ fontSize: 32, color: "primary.main" }} />
            <Typography variant="h4" component="h1">
              Escaneo de Red
            </Typography>
          </Box>
          <Typography variant="body1" color="text.secondary">
            Descubre dispositivos en tu red local y encuentra cámaras IP disponibles
          </Typography>
        </Box>
      </Fade>

      {/* Contenido principal con dos columnas */}
      <Box
        sx={{
          flex: 1,
          display: "grid",
          gridTemplateColumns: { xs: "1fr", lg: "1fr 380px" },
          gap: 2,
          minHeight: 0,
        }}
      >
        {/* Columna principal - Panel de escaneo */}
        <Paper
          sx={{
            p: 3,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            borderRadius: borderTokens.radius.lg,
          }}
        >
          <NetworkScanPanel 
            onComplete={() => {
              // Opcionalmente navegar automáticamente
              if (selectedIP) {
                handlePortScanNavigation();
              }
            }}
            isScanning={isScanning}
            progress={scanProgress}
          />

          {/* Acciones adicionales */}
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
              startIcon={<RefreshIcon />}
              onClick={handleRefresh}
              disabled={isScanning}
              sx={{ textTransform: "none" }}
            >
              Actualizar resultados
            </Button>

            <Button
              variant="contained"
              onClick={handlePortScanNavigation}
              disabled={!selectedIP}
              sx={{ textTransform: "none" }}
            >
              Continuar con escaneo de puertos
            </Button>
          </Box>
        </Paper>

        {/* Columna lateral - Resumen y resultados */}
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2, minHeight: 0 }}>
          {/* Panel de resumen */}
          <Paper
            sx={{
              p: 2,
              backgroundColor: theme.palette.mode === "dark"
                ? colorTokens.background.darkElevated
                : colorTokens.background.lightElevated,
              borderRadius: borderTokens.radius.lg,
            }}
          >
            <ScanSummary 
              totalDevices={scanResults.length}
              possibleCameras={possibleCameras}
              activeStep={0}
              scanProgress={scanProgress}
            />
          </Paper>

          {/* Panel de resultados */}
          <Paper
            sx={{
              p: 2,
              flex: 1,
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
              borderRadius: borderTokens.radius.lg,
            }}
          >
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
              <Typography variant="subtitle1" fontWeight={600}>
                Dispositivos Encontrados
              </Typography>
              {selectedIP && (
                <Chip 
                  label={`IP seleccionada: ${selectedIP}`}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              )}
            </Box>
            
            <Box sx={{ flex: 1, overflow: "auto" }}>
              <ScanResults 
                results={scanResults as DeviceScanResult[]}
                onSelectIP={handleIPSelection}
                selectedIP={selectedIP}
              />
            </Box>
          </Paper>
        </Box>
      </Box>
    </Container>
  );
});

// Añadir displayName para debugging
NetworkScanPage.displayName = 'NetworkScanPage';

export default NetworkScanPage;