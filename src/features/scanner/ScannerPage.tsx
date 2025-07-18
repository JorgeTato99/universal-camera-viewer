/**
 * 🎯 Scanner Index Page - Universal Camera Viewer
 * Página índice del escáner con opciones de diferentes tipos de escaneo
 * Optimizada con memo y navegación eficiente
 */

import React, { memo, useCallback } from "react";
import {
  Box,
  Typography,
  Paper,
  Grid2 as Grid,
  Button,
  Card,
  CardContent,
  CardActions,
  Fade,
  useTheme,
  Container,
  Chip,
  alpha,
  Stack,
} from "@mui/material";
import {
  Search as SearchIcon,
  NetworkCheck as NetworkIcon,
  PortableWifiOff as PortIcon,
  VpnKey as AccessIcon,
  ArrowForward as ArrowForwardIcon,
  TipsAndUpdates as TipsIcon,
  CheckCircle as CheckIcon,
} from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import { colorTokens, spacingTokens, borderTokens } from "../../design-system/tokens";

interface ScanOption {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  path: string;
  color: string;
  features: string[];
  step: number;
}

const scanOptions: ScanOption[] = [
  {
    id: "network",
    title: "Escaneo de Red",
    description: "Descubre todos los dispositivos conectados a tu red local e identifica posibles cámaras IP",
    icon: <NetworkIcon sx={{ fontSize: 40 }} />,
    path: "/scanner/network",
    color: colorTokens.primary[500],
    step: 1,
    features: [
      "Detección automática",
      "Identificación de cámaras",
      "Análisis de rangos IP",
      "Info de fabricante",
    ],
  },
  {
    id: "ports",
    title: "Escaneo de Puertos",
    description: "Analiza los puertos abiertos en dispositivos específicos para identificar servicios",
    icon: <PortIcon sx={{ fontSize: 40 }} />,
    path: "/scanner/ports",
    color: colorTokens.secondary[500],
    step: 2,
    features: [
      "Servicios ONVIF",
      "Identificación RTSP",
      "Puertos comunes",
      "Detección de protocolos",
    ],
  },
  {
    id: "access",
    title: "Prueba de Acceso",
    description: "Verifica credenciales y establece conexión con las cámaras detectadas en tu red",
    icon: <AccessIcon sx={{ fontSize: 40 }} />,
    path: "/scanner/access",
    color: colorTokens.status.connected,
    step: 3,
    features: [
      "Prueba credenciales",
      "Verificación protocolos",
      "Test conectividad",
      "Config automática",
    ],
  },
];

const ScannerPage = memo(() => {
  const theme = useTheme();
  const navigate = useNavigate();

  const handleNavigate = useCallback((path: string) => {
    navigate(path);
  }, [navigate]);

  const handleQuickScan = useCallback(() => {
    // Navegar directamente al escaneo de red como inicio rápido
    navigate("/scanner/network");
  }, [navigate]);

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      {/* Header */}
      <Fade in timeout={600}>
        <Box sx={{ mb: 5, textAlign: "center" }}>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 2, mb: 2 }}>
            <SearchIcon sx={{ fontSize: 56, color: "primary.main" }} />
            <Typography variant="h3" component="h1" fontWeight={600}>
              Centro de Escaneo
            </Typography>
          </Box>
          <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600, mx: "auto" }}>
            Descubre y configura cámaras IP en tu red de forma automática
          </Typography>
        </Box>
      </Fade>

      {/* Botón de escaneo rápido */}
      <Fade in timeout={800}>
        <Box sx={{ display: "flex", justifyContent: "center", mb: 5 }}>
          <Button
            variant="contained"
            size="large"
            startIcon={<SearchIcon />}
            onClick={handleQuickScan}
            sx={{
              px: 4,
              py: 1.5,
              fontSize: "1.1rem",
              fontWeight: 500,
              textTransform: "none",
              borderRadius: 2,
              background: `linear-gradient(135deg, ${colorTokens.primary[500]} 0%, ${colorTokens.primary[600]} 100%)`,
              boxShadow: `0 4px 14px 0 ${alpha(colorTokens.primary[500], 0.4)}`,
              "&:hover": {
                background: `linear-gradient(135deg, ${colorTokens.primary[600]} 0%, ${colorTokens.primary[700]} 100%)`,
                boxShadow: `0 6px 20px 0 ${alpha(colorTokens.primary[600], 0.4)}`,
                transform: "translateY(-2px)",
              },
              transition: "all 0.3s ease",
            }}
          >
            Iniciar Escaneo Completo
          </Button>
        </Box>
      </Fade>

      {/* Grid de opciones */}
      <Grid container spacing={3} sx={{ mb: 5, width: '100%' }}>
        {scanOptions.map((option, index) => (
          <Grid size={{ xs: 12, md: 4 }} key={option.id}>
            <Fade in timeout={1000 + index * 200}>
              <Card
                sx={{
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  borderRadius: 2,
                  transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                  border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
                  overflow: "hidden",
                  position: "relative",
                  "&:hover": {
                    transform: "translateY(-8px)",
                    boxShadow: `0 12px 24px ${alpha(option.color, 0.15)}`,
                    borderColor: alpha(option.color, 0.3),
                    "& .scan-option-icon": {
                      transform: "scale(1.1) rotate(5deg)",
                    },
                  },
                }}
              >
                {/* Indicador de paso */}
                <Box
                  sx={{
                    position: "absolute",
                    top: 12,
                    right: 12,
                    width: 32,
                    height: 32,
                    borderRadius: "50%",
                    backgroundColor: alpha(option.color, 0.1),
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "0.875rem",
                    fontWeight: 600,
                    color: option.color,
                  }}
                >
                  {option.step}
                </Box>

                <CardContent sx={{ flex: 1, p: 3, textAlign: "center" }}>
                  {/* Icono */}
                  <Box
                    className="scan-option-icon"
                    sx={{
                      width: 80,
                      height: 80,
                      borderRadius: "50%",
                      backgroundColor: alpha(option.color, 0.1),
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      mx: "auto",
                      mb: 3,
                      color: option.color,
                      transition: "all 0.3s ease",
                    }}
                  >
                    {option.icon}
                  </Box>
                  
                  {/* Título */}
                  <Typography 
                    variant="h5" 
                    component="h2" 
                    gutterBottom 
                    fontWeight={600}
                    sx={{ mb: 1.5 }}
                  >
                    {option.title}
                  </Typography>
                  
                  {/* Descripción */}
                  <Typography 
                    variant="body2" 
                    color="text.secondary" 
                    sx={{ 
                      mb: 3,
                      minHeight: 60, // Aumentar altura para acomodar textos más largos
                      lineHeight: 1.5,
                      px: 2, // Padding horizontal para mejor lectura
                    }}
                  >
                    {option.description}
                  </Typography>

                  {/* Features como lista */}
                  <Stack spacing={0.75} sx={{ minHeight: 120 }}>
                    {option.features.map((feature, idx) => (
                      <Box
                        key={feature}
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "flex-start", // Alinear a la izquierda
                          gap: 1,
                          px: 2, // Padding horizontal consistente
                          py: 0.25,
                        }}
                      >
                        <CheckIcon 
                          sx={{ 
                            fontSize: 14, 
                            color: option.color,
                            opacity: 0.8,
                            flexShrink: 0,
                          }} 
                        />
                        <Typography 
                          variant="caption" 
                          sx={{ 
                            fontSize: "0.813rem",
                            color: "text.secondary",
                            lineHeight: 1.4,
                          }}
                        >
                          {feature}
                        </Typography>
                      </Box>
                    ))}
                  </Stack>
                </CardContent>
                
                {/* Acción */}
                <CardActions 
                  sx={{ 
                    px: 3, 
                    pb: 3, 
                    pt: 0,
                    justifyContent: "center" 
                  }}
                >
                  <Button
                    variant="outlined"
                    fullWidth
                    endIcon={<ArrowForwardIcon />}
                    onClick={() => handleNavigate(option.path)}
                    sx={{
                      borderColor: alpha(option.color, 0.5),
                      color: option.color,
                      textTransform: "none",
                      py: 1,
                      fontSize: "0.938rem",
                      fontWeight: 500,
                      "&:hover": {
                        borderColor: option.color,
                        backgroundColor: alpha(option.color, 0.05),
                      },
                    }}
                  >
                    Comenzar
                  </Button>
                </CardActions>
              </Card>
            </Fade>
          </Grid>
        ))}
      </Grid>

      {/* Sección de ayuda */}
      <Fade in timeout={1600}>
        <Paper
          sx={{
            p: 4,
            backgroundColor: theme.palette.mode === "dark"
              ? alpha(colorTokens.background.darkElevated, 0.5)
              : alpha(colorTokens.background.lightElevated, 0.5),
            borderRadius: 2,
            border: `1px solid ${alpha(theme.palette.divider, 0.3)}`,
            backdropFilter: "blur(10px)",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "flex-start", gap: 3 }}>
            <TipsIcon 
              sx={{ 
                color: "primary.main", 
                mt: 0.5,
                fontSize: 28,
              }} 
            />
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" gutterBottom fontWeight={600}>
                ¿Cómo empezar?
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                El proceso de descubrimiento de cámaras es simple y se realiza en tres pasos:
              </Typography>
              
              <Grid container spacing={3} sx={{ mt: 1 }}>
                {scanOptions.map((option) => (
                  <Grid size={{ xs: 12, sm: 4 }} key={option.id}>
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "flex-start",
                        gap: 1.5,
                      }}
                    >
                      <Box
                        sx={{
                          width: 28,
                          height: 28,
                          borderRadius: "50%",
                          backgroundColor: alpha(option.color, 0.1),
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: "0.875rem",
                          fontWeight: 600,
                          color: option.color,
                          flexShrink: 0,
                        }}
                      >
                        {option.step}
                      </Box>
                      <Box>
                        <Typography 
                          variant="subtitle2" 
                          fontWeight={600} 
                          gutterBottom
                          sx={{ color: option.color }}
                        >
                          {option.title}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {option.step === 1 && "Encuentra todos los dispositivos conectados a tu red local"}
                          {option.step === 2 && "Identifica los servicios de cámara analizando puertos"}
                          {option.step === 3 && "Conecta y configura las cámaras con credenciales válidas"}
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </Box>
          </Box>
        </Paper>
      </Fade>
    </Container>
  );
});

// Añadir displayName para debugging
ScannerPage.displayName = 'ScannerPage';

export default ScannerPage;