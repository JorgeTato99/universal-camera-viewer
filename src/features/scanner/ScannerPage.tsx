/**
 * 🎯 Scanner Page - Universal Camera Viewer
 * Página principal para escaneo de red y descubrimiento de cámaras
 */

import React, { useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Divider,
  useTheme,
  Fade,
  Zoom,
  alpha,
  keyframes,
} from "@mui/material";
import {
  Search as SearchIcon,
  NetworkCheck as NetworkIcon,
  PortableWifiOff as PortIcon,
  VpnKey as AccessIcon,
  ArrowForward as NextIcon,
  ArrowBack as BackIcon,
} from "@mui/icons-material";
import { colorTokens, spacingTokens, borderTokens } from "../../design-system/tokens";
import { NetworkScanPanel } from "./components/NetworkScanPanel";
import { PortScanPanel } from "./components/PortScanPanel";
import { AccessTestPanel } from "./components/AccessTestPanel";
import { ScanResults } from "./components/ScanResults";
import { ScanSummary } from "./components/ScanSummary";
import { useScannerStore } from "../../stores/scannerStore";
import { ScanStatus, DeviceScanResult } from "../../types/scanner.types";

// Animaciones personalizadas
const slideInLeft = keyframes`
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
`;

const pulseAnimation = keyframes`
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
`;

// Pasos del proceso de escaneo
const scanSteps = [
  {
    label: "Escaneo de Red",
    icon: <NetworkIcon />,
    description: "Buscar dispositivos en la red local",
  },
  {
    label: "Escaneo de Puertos",
    icon: <PortIcon />,
    description: "Analizar puertos en IPs detectadas",
  },
  {
    label: "Prueba de Acceso",
    icon: <AccessIcon />,
    description: "Verificar credenciales y conexión",
  },
];

const ScannerPage: React.FC = () => {
  const theme = useTheme();
  const [activeStep, setActiveStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  
  /**
   * INTEGRACIÓN CON BACKEND:
   * 
   * El estado del scanner debe venir del store global (Zustand).
   * El store se conecta con el servicio ScannerService para:
   * 1. Iniciar escaneos
   * 2. Recibir actualizaciones por WebSocket
   * 3. Obtener resultados
   * 
   * TODO: Implementar las siguientes acciones en el store:
   * - startNetworkScan(config)
   * - startPortScan(ip, config)
   * - testAccess(ip, port, credentials)
   * - selectDevice(device)
   * - cancelScan()
   */
  
  // Estado del store
  const currentScan = useScannerStore((state) => state.currentScan);
  const scanResults = useScannerStore((state) => state.results) || [];
  const selectedDevice = useScannerStore((state) => state.selectedDevice);
  
  // Estados derivados
  const isScanning = currentScan?.status === ScanStatus.SCANNING;
  const scanProgress = currentScan?.progress?.scanned_ips 
    ? Math.round((currentScan.progress.scanned_ips / currentScan.progress.total_ips) * 100)
    : 0;
  const selectedIP = selectedDevice?.ip || "";
  
  // Estado local solo para UI
  const [selectedIPLocal, setSelectedIPLocal] = useState<string>("");

  const handleNext = () => {
    if (activeStep < scanSteps.length - 1) {
      setCompletedSteps([...completedSteps, activeStep]);
      setActiveStep(activeStep + 1);
    }
  };

  const handleBack = () => {
    if (activeStep > 0) {
      setActiveStep(activeStep - 1);
    }
  };

  const handleStepClick = (step: number) => {
    // Solo permitir navegar a pasos completados o el siguiente al último completado
    const maxAllowedStep = completedSteps.length > 0 
      ? Math.max(...completedSteps) + 1 
      : 0;
    
    if (step <= maxAllowedStep && step < scanSteps.length) {
      setActiveStep(step);
    }
  };

  const isStepCompleted = (step: number) => completedSteps.includes(step);

  return (
    <Box
      sx={{
        p: 2,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        gap: 2,
      }}
    >
      {/* Header con animación */}
      <Fade in timeout={600}>
        <Box>
          <Typography
            variant="h5"
            sx={{
              fontWeight: 600,
              color: theme.palette.text.primary,
              mb: 0.5,
              animation: `${slideInLeft} 0.6s ease-out`,
            }}
          >
            Escáner de Red
          </Typography>
          <Typography
            variant="body2"
            sx={{
              color: theme.palette.text.secondary,
              animation: `${slideInLeft} 0.8s ease-out`,
            }}
          >
            Descubre y configura cámaras IP en tu red local de forma automática
          </Typography>
        </Box>
      </Fade>

      {/* Contenido principal con dos columnas */}
      <Box
        sx={{
          flex: 1,
          display: "grid",
          gridTemplateColumns: "1fr 380px",
          gap: 2,
          minHeight: 0, // Importante para que el scroll funcione
        }}
      >
        {/* Columna izquierda - Stepper y paneles */}
        <Zoom in timeout={400}>
          <Paper
            sx={{
              p: 3,
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
              borderRadius: borderTokens.radius.lg,
              transition: "box-shadow 0.3s ease",
              "&:hover": {
                boxShadow: theme.shadows[4],
              },
            }}
          >
          {/* Stepper horizontal compacto */}
          <Box sx={{ mb: 3 }}>
            <Stepper activeStep={activeStep} alternativeLabel>
              {scanSteps.map((step, index) => (
                <Step 
                  key={step.label} 
                  completed={isStepCompleted(index)}
                  sx={{ cursor: "pointer" }}
                  onClick={() => handleStepClick(index)}
                >
                  <StepLabel
                    StepIconComponent={() => (
                      <Box
                        sx={{
                          width: 40,
                          height: 40,
                          borderRadius: "50%",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          backgroundColor:
                            activeStep === index
                              ? colorTokens.primary[500]
                              : isStepCompleted(index)
                              ? colorTokens.status.connected
                              : theme.palette.action.disabledBackground,
                          color: "#fff",
                          transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                          transform: activeStep === index ? "scale(1.1)" : "scale(1)",
                          boxShadow: activeStep === index 
                            ? `0 0 0 4px ${alpha(colorTokens.primary[500], 0.2)}`
                            : "none",
                          animation: activeStep === index ? `${pulseAnimation} 2s infinite` : "none",
                          "&:hover": {
                            transform: "scale(1.05)",
                            boxShadow: `0 0 0 4px ${alpha(theme.palette.primary.main, 0.1)}`,
                          },
                          "& svg": {
                            fontSize: 20,
                            transition: "transform 0.3s ease",
                          },
                        }}
                      >
                        {step.icon}
                      </Box>
                    )}
                  >
                    <Typography
                      variant="caption"
                      sx={{
                        fontWeight: activeStep === index ? 600 : 400,
                        color:
                          activeStep === index
                            ? theme.palette.text.primary
                            : theme.palette.text.secondary,
                      }}
                    >
                      {step.label}
                    </Typography>
                  </StepLabel>
                </Step>
              ))}
            </Stepper>
          </Box>

          <Divider sx={{ mb: 3 }} />

          {/* Panel de contenido según el paso activo */}
          <Box sx={{ flex: 1, overflow: "auto", position: "relative" }}>
            <Fade in={activeStep === 0} timeout={500} unmountOnExit>
              <Box sx={{ position: activeStep === 0 ? "relative" : "absolute", width: "100%" }}>
                <NetworkScanPanel 
                  onComplete={handleNext}
                  isScanning={isScanning}
                  progress={scanProgress}
                />
              </Box>
            </Fade>
            <Fade in={activeStep === 1} timeout={500} unmountOnExit>
              <Box sx={{ position: activeStep === 1 ? "relative" : "absolute", width: "100%" }}>
                <PortScanPanel
                  selectedIP={selectedIP}
                  onComplete={handleNext}
                  onBack={handleBack}
                />
              </Box>
            </Fade>
            <Fade in={activeStep === 2} timeout={500} unmountOnExit>
              <Box sx={{ position: activeStep === 2 ? "relative" : "absolute", width: "100%" }}>
                <AccessTestPanel
                  selectedIP={selectedIP}
                  onComplete={() => {
                    setCompletedSteps([...completedSteps, activeStep]);
                  }}
                  onBack={handleBack}
                />
              </Box>
            </Fade>
          </Box>

          {/* Botones de navegación */}
          <Fade in timeout={800}>
            <Box
              sx={{
                mt: 3,
                pt: 2,
                borderTop: `1px solid ${theme.palette.divider}`,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <Button
                disabled={activeStep === 0}
                onClick={handleBack}
                startIcon={<BackIcon />}
                sx={{ 
                  textTransform: "none",
                  transition: "all 0.3s ease",
                  "&:hover:not(:disabled)": {
                    transform: "translateX(-4px)",
                  },
                }}
              >
                Atrás
              </Button>

            <Typography variant="caption" color="text.secondary">
              Paso {activeStep + 1} de {scanSteps.length}
            </Typography>

              <Button
                disabled={activeStep === scanSteps.length - 1}
                onClick={handleNext}
                endIcon={<NextIcon />}
                variant="contained"
                sx={{ 
                  textTransform: "none",
                  transition: "all 0.3s ease",
                  "&:hover:not(:disabled)": {
                    transform: "translateX(4px)",
                  },
                }}
              >
                Siguiente
              </Button>
            </Box>
          </Fade>
          </Paper>
        </Zoom>

        {/* Columna derecha - Resultados y resumen */}
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 2,
            minHeight: 0,
          }}
        >
          {/* Panel de resumen */}
          <Zoom in timeout={600} style={{ transitionDelay: "200ms" }}>
            <Paper
              sx={{
                p: 2,
                backgroundColor: theme.palette.mode === "dark"
                  ? colorTokens.background.darkElevated
                  : colorTokens.background.lightElevated,
                borderRadius: borderTokens.radius.lg,
                transition: "all 0.3s ease",
                "&:hover": {
                  boxShadow: theme.shadows[2],
                },
              }}
            >
            <ScanSummary 
              totalDevices={scanResults.length}
              possibleCameras={scanResults.filter((r: any) => r.probability > 0.7).length}
              activeStep={activeStep}
              scanProgress={scanProgress}
            />
            </Paper>
          </Zoom>

          {/* Panel de resultados */}
          <Zoom in timeout={700} style={{ transitionDelay: "300ms" }}>
            <Paper
              sx={{
                p: 2,
                flex: 1,
                overflow: "hidden",
                display: "flex",
                flexDirection: "column",
                borderRadius: borderTokens.radius.lg,
                transition: "all 0.3s ease",
                "&:hover": {
                  boxShadow: theme.shadows[2],
                },
              }}
            >
              <Typography
                variant="subtitle2"
                sx={{
                  fontWeight: 600,
                  mb: 1,
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                }}
              >
                <SearchIcon 
                  fontSize="small" 
                  sx={{ 
                    color: colorTokens.primary[500],
                    animation: isScanning ? `${pulseAnimation} 2s infinite` : "none",
                  }} 
                />
                Dispositivos Encontrados
              </Typography>
            
            <Box sx={{ flex: 1, overflow: "auto" }}>
              <ScanResults 
                results={scanResults as DeviceScanResult[]}
                onSelectIP={(ip) => {
                  // TODO: Implementar selectDevice en el store
                  setSelectedIPLocal(ip);
                  // useScannerStore.getState().selectDevice(device);
                }}
                selectedIP={selectedIPLocal || selectedIP}
              />
              </Box>
            </Paper>
          </Zoom>
        </Box>
      </Box>
    </Box>
  );
};

export default ScannerPage;
