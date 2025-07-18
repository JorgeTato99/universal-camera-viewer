/**
 * 🔐 Access Test Page - Universal Camera Viewer
 * Página dedicada a la prueba de acceso y credenciales de cámaras
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
  Alert,
  AlertTitle,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from "@mui/material";
import {
  VpnKey as AccessIcon,
  NavigateNext as NavigateNextIcon,
  ArrowBack as BackIcon,
  CheckCircle as SuccessIcon,
  Cancel as ErrorIcon,
  AddCircle as AddIcon,
  Home as HomeIcon,
} from "@mui/icons-material";
import { useNavigate, useSearchParams } from "react-router-dom";
import { colorTokens, spacingTokens, borderTokens } from "../../../../design-system/tokens";
import { AccessTestPanel } from "../../components/AccessTestPanel";
import { useScannerStore } from "../../../../stores/scannerStore";
import { useNotificationStore } from "../../../../stores/notificationStore";

interface TestResult {
  protocol: string;
  port: number;
  username: string;
  success: boolean;
  message?: string;
}

const AccessTestPage = memo(() => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { addNotification } = useNotificationStore();
  
  // Obtener parámetros de URL
  const ipFromUrl = searchParams.get('ip');
  const portsFromUrl = searchParams.get('ports');
  const selectedDevice = useScannerStore((state) => state.selectedDevice);
  
  const targetIP = ipFromUrl || selectedDevice?.ip || "";
  const targetPorts = useMemo(() => {
    if (portsFromUrl) {
      return portsFromUrl.split(',').map(p => parseInt(p)).filter(p => !isNaN(p));
    }
    return selectedDevice?.openPorts || [];
  }, [portsFromUrl, selectedDevice]);

  // Estado local
  const [testComplete, setTestComplete] = useState(false);
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [successfulAccess, setSuccessfulAccess] = useState<TestResult | null>(null);

  // Verificar si tenemos datos válidos
  const hasValidData = useMemo(() => {
    if (!targetIP) return false;
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
    return ipRegex.test(targetIP) && targetPorts.length > 0;
  }, [targetIP, targetPorts]);

  // Handlers
  const handleComplete = useCallback(() => {
    setTestComplete(true);
    // Buscar si hay algún acceso exitoso
    const successful = testResults.find(r => r.success);
    if (successful) {
      setSuccessfulAccess(successful);
      addNotification({
        type: 'success',
        message: `¡Acceso exitoso! Protocolo: ${successful.protocol}, Puerto: ${successful.port}`,
      });
    }
  }, [testResults, addNotification]);

  const handleAddResult = useCallback((result: TestResult) => {
    setTestResults(prev => [...prev, result]);
  }, []);

  const handleBack = useCallback(() => {
    navigate(`/scanner/ports?ip=${targetIP}`);
  }, [navigate, targetIP]);

  const handleAddCamera = useCallback(() => {
    if (successfulAccess) {
      // Navegar a registro de cámaras con los datos
      const params = new URLSearchParams({
        ip: targetIP,
        port: successfulAccess.port.toString(),
        protocol: successfulAccess.protocol,
        username: successfulAccess.username,
      });
      navigate(`/cameras/register?${params.toString()}`);
    }
  }, [successfulAccess, targetIP, navigate]);

  const handleNewScan = useCallback(() => {
    navigate("/scanner/network");
  }, [navigate]);

  // Si no hay datos válidos, mostrar mensaje
  if (!hasValidData) {
    return (
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Alert severity="warning" sx={{ maxWidth: 600, mx: "auto" }}>
          <AlertTitle>Datos insuficientes</AlertTitle>
          Debes completar el escaneo de red y puertos antes de probar el acceso.
          <Box sx={{ mt: 2 }}>
            <Button
              variant="contained"
              startIcon={<BackIcon />}
              onClick={() => navigate("/scanner/network")}
            >
              Volver al escaneo de red
            </Button>
          </Box>
        </Alert>
      </Container>
    );
  }

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
        <Link
          component="button"
          variant="body2"
          onClick={() => navigate(`/scanner/ports?ip=${targetIP}`)}
          sx={{ 
            textDecoration: "none",
            color: "text.secondary",
            "&:hover": { color: "primary.main" }
          }}
        >
          Escaneo de Puertos
        </Link>
        <Typography color="text.primary" variant="body2">
          Prueba de Acceso
        </Typography>
      </Breadcrumbs>

      {/* Header */}
      <Fade in timeout={600}>
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
            <AccessIcon sx={{ fontSize: 32, color: "primary.main" }} />
            <Typography variant="h4" component="h1">
              Prueba de Acceso
            </Typography>
            <Chip 
              label={`IP: ${targetIP}`}
              color="primary"
              variant="outlined"
              sx={{ ml: 2 }}
            />
          </Box>
          <Typography variant="body1" color="text.secondary">
            Verifica las credenciales y la conexión con la cámara detectada
          </Typography>
        </Box>
      </Fade>

      {/* Contenido principal */}
      <Box sx={{ flex: 1, display: "grid", gridTemplateColumns: { xs: "1fr", lg: "2fr 1fr" }, gap: 2 }}>
        {/* Panel principal */}
        <Paper
          sx={{
            p: 3,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            borderRadius: borderTokens.radius.lg,
          }}
        >
          <AccessTestPanel
            selectedIP={targetIP}
            onComplete={handleComplete}
            onBack={handleBack}
            onTestResult={handleAddResult}
          />

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
              Volver al escaneo de puertos
            </Button>

            <Box sx={{ display: "flex", gap: 2 }}>
              <Button
                startIcon={<HomeIcon />}
                onClick={handleNewScan}
                sx={{ textTransform: "none" }}
              >
                Nuevo escaneo
              </Button>
              
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleAddCamera}
                disabled={!successfulAccess}
                sx={{ textTransform: "none" }}
              >
                Agregar cámara
              </Button>
            </Box>
          </Box>
        </Paper>

        {/* Panel lateral - Resultados */}
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {/* Resumen de puertos a probar */}
          <Card sx={{ borderRadius: borderTokens.radius.lg }}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                Puertos a probar
              </Typography>
              <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mt: 1 }}>
                {targetPorts.map((port) => (
                  <Chip
                    key={port}
                    label={`Puerto ${port}`}
                    size="small"
                    variant="outlined"
                  />
                ))}
              </Box>
            </CardContent>
          </Card>

          {/* Resultados de las pruebas */}
          {testResults.length > 0 && (
            <Card sx={{ borderRadius: borderTokens.radius.lg, flex: 1, overflow: "hidden" }}>
              <CardContent sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
                <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                  Resultados de pruebas
                </Typography>
                <List sx={{ flex: 1, overflow: "auto" }}>
                  {testResults.map((result, index) => (
                    <React.Fragment key={index}>
                      <ListItem>
                        <ListItemIcon>
                          {result.success ? (
                            <SuccessIcon sx={{ color: colorTokens.status.connected }} />
                          ) : (
                            <ErrorIcon sx={{ color: colorTokens.status.error }} />
                          )}
                        </ListItemIcon>
                        <ListItemText
                          primary={`${result.protocol} - Puerto ${result.port}`}
                          secondary={
                            <Box>
                              <Typography variant="caption" component="span">
                                Usuario: {result.username}
                              </Typography>
                              {result.message && (
                                <Typography variant="caption" display="block" color="text.secondary">
                                  {result.message}
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                      </ListItem>
                      {index < testResults.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              </CardContent>
            </Card>
          )}

          {/* Mensaje de éxito */}
          {successfulAccess && (
            <Alert 
              severity="success" 
              action={
                <Button color="inherit" size="small" onClick={handleAddCamera}>
                  Agregar
                </Button>
              }
            >
              <AlertTitle>¡Conexión exitosa!</AlertTitle>
              Puedes agregar esta cámara a tu sistema.
            </Alert>
          )}
        </Box>
      </Box>
    </Container>
  );
});

// Añadir displayName para debugging
AccessTestPage.displayName = 'AccessTestPage';

export default AccessTestPage;