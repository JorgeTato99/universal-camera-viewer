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
  TextField,
  InputAdornment,
} from "@mui/material";
import {
  VpnKey as AccessIcon,
  NavigateNext as NavigateNextIcon,
  ArrowBack as BackIcon,
  CheckCircle as SuccessIcon,
  Cancel as ErrorIcon,
  AddCircle as AddIcon,
  Home as HomeIcon,
  Router as RouterIcon,
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
  const [manualIP, setManualIP] = useState("");
  const [ipError, setIpError] = useState("");
  const [manualPorts, setManualPorts] = useState("");
  const [portsError, setPortsError] = useState("");
  const [useManualData, setUseManualData] = useState(!targetIP || targetPorts.length === 0);

  // Validar formato de IP
  const validateIP = useCallback((ip: string): boolean => {
    if (!ip) return false;
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipRegex.test(ip)) return false;
    
    const octets = ip.split('.');
    return octets.every(octet => {
      const num = parseInt(octet, 10);
      return num >= 0 && num <= 255;
    });
  }, []);

  // Validar formato de puertos
  const validatePorts = useCallback((ports: string): number[] => {
    if (!ports.trim()) return [];
    
    const portList = ports.split(',').map(p => p.trim());
    const validPorts: number[] = [];
    
    for (const port of portList) {
      const num = parseInt(port, 10);
      if (!isNaN(num) && num > 0 && num <= 65535) {
        validPorts.push(num);
      }
    }
    
    return validPorts;
  }, []);

  // IP y puertos finales a usar
  const finalIP = useManualData ? manualIP : targetIP;
  const finalPorts = useMemo(() => {
    if (useManualData) {
      return validatePorts(manualPorts);
    }
    return targetPorts;
  }, [useManualData, manualPorts, targetPorts, validatePorts]);

  // Verificar si tenemos datos válidos
  const hasValidData = useMemo(() => {
    return validateIP(finalIP) && finalPorts.length > 0;
  }, [finalIP, finalPorts, validateIP]);

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
    navigate(`/scanner/ports?ip=${finalIP}`);
  }, [navigate, finalIP]);

  const handleAddCamera = useCallback(() => {
    if (successfulAccess) {
      // Navegar a registro de cámaras con los datos
      const params = new URLSearchParams({
        ip: finalIP,
        port: successfulAccess.port.toString(),
        protocol: successfulAccess.protocol,
        username: successfulAccess.username,
      });
      navigate(`/cameras/register?${params.toString()}`);
    }
  }, [successfulAccess, finalIP, navigate]);

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

  // Manejar cambio de puertos manuales
  const handlePortsChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setManualPorts(value);
    
    if (value) {
      const validPorts = validatePorts(value);
      if (validPorts.length === 0) {
        setPortsError("Ingresa puertos válidos separados por comas (ej: 80, 554, 8000)");
      } else {
        setPortsError("");
      }
    } else {
      setPortsError("");
    }
  }, [validatePorts]);

  // Alternar entre datos manuales y automáticos
  const handleToggleManualData = useCallback(() => {
    setUseManualData(!useManualData);
    setManualIP("");
    setManualPorts("");
    setIpError("");
    setPortsError("");
    setTestComplete(false);
    setTestResults([]);
    setSuccessfulAccess(null);
  }, [useManualData]);


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
          onClick={() => navigate(`/scanner/ports?ip=${finalIP}`)}
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
            {hasValidData && (
              <Chip 
                label={`IP: ${finalIP}`}
                color="primary"
                variant="outlined"
                sx={{ ml: 2 }}
              />
            )}
          </Box>
          <Typography variant="body1" color="text.secondary">
            Verifica las credenciales y la conexión con la cámara
          </Typography>
        </Box>
      </Fade>

      {/* Contenido principal */}
      <Box sx={{ flex: 1, display: "flex", flexDirection: "column", gap: 2 }}>
        {/* Opción de entrada manual de datos */}
        {(!targetIP || !targetPorts.length || useManualData) && (
          <Fade in timeout={600}>
            <Paper
              sx={{
                p: 3,
                borderRadius: borderTokens.radius.lg,
                backgroundColor: theme.palette.mode === "dark"
                  ? colorTokens.background.darkElevated
                  : colorTokens.background.lightElevated,
              }}
            >
              <Typography variant="h6" gutterBottom>
                Configuración de prueba
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {targetIP || targetPorts.length > 0
                  ? "Se detectaron datos del escaneo previo, pero puedes ingresar datos diferentes si lo deseas."
                  : "No se detectaron datos del escaneo previo. Ingresa manualmente la IP y puertos a probar."
                }
              </Typography>
              
              <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <TextField
                  label="Dirección IP"
                  value={manualIP}
                  onChange={handleIPChange}
                  error={!!ipError}
                  helperText={ipError || "Ejemplo: 192.168.1.100"}
                  placeholder="192.168.1.100"
                  sx={{ maxWidth: 300 }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <RouterIcon sx={{ fontSize: 20 }} />
                      </InputAdornment>
                    ),
                  }}
                />
                
                <TextField
                  label="Puertos a probar"
                  value={manualPorts}
                  onChange={handlePortsChange}
                  error={!!portsError}
                  helperText={portsError || "Ingresa puertos separados por comas"}
                  placeholder="80, 554, 8000, 2020"
                  sx={{ maxWidth: 400 }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <AccessIcon sx={{ fontSize: 20 }} />
                      </InputAdornment>
                    ),
                  }}
                />
                
                {(targetIP || targetPorts.length > 0) && (
                  <Button
                    variant="outlined"
                    onClick={handleToggleManualData}
                    sx={{ alignSelf: "flex-start" }}
                  >
                    {useManualData ? "Usar datos detectados" : "Usar otros datos"}
                  </Button>
                )}
              </Box>
              
              {(targetIP || targetPorts.length > 0) && !useManualData && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  Usando datos detectados: <strong>{targetIP}</strong> - Puertos: <strong>{targetPorts.join(', ')}</strong>
                </Alert>
              )}
            </Paper>
          </Fade>
        )}

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
            {hasValidData ? (
              <AccessTestPanel
                selectedIP={finalIP}
                onComplete={handleComplete}
                onBack={handleBack}
                onTestResult={handleAddResult}
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
                <AccessIcon sx={{ fontSize: 64, color: "text.secondary", mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Ingresa los datos necesarios para comenzar
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Necesitas especificar una dirección IP válida y al menos un puerto para probar el acceso.
                </Typography>
              </Box>
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
                {finalPorts.map((port) => (
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
      </Box>
    </Container>
  );
});

// Añadir displayName para debugging
AccessTestPage.displayName = 'AccessTestPage';

export default AccessTestPage;