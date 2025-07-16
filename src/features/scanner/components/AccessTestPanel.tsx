/**
 * 🎯 Access Test Panel - Universal Camera Viewer
 * Panel para probar credenciales y acceso a la cámara
 */

import React, { useState } from "react";
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Alert,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  InputAdornment,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Collapse,
  Divider,
  Tooltip,
} from "@mui/material";
import {
  VpnKey as KeyIcon,
  Visibility,
  VisibilityOff,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  PlayArrow as TestIcon,
  Save as SaveIcon,
  AccountCircle as UserIcon,
  Lock as PasswordIcon,
  Language as ProtocolIcon,
  ExpandMore,
  ExpandLess,
} from "@mui/icons-material";
import { colorTokens } from "../../../design-system/tokens";

interface AccessTestPanelProps {
  selectedIP?: string;
  onComplete: () => void;
  onBack: () => void;
}

interface TestResult {
  protocol: string;
  port: number;
  status: "testing" | "success" | "failed" | "pending";
  message?: string;
  details?: {
    manufacturer?: string;
    model?: string;
    firmware?: string;
    capabilities?: string[];
  };
}

// Credenciales comunes por defecto
const DEFAULT_CREDENTIALS = [
  { username: "admin", password: "admin", brand: "Genérico" },
  { username: "admin", password: "12345", brand: "Genérico" },
  { username: "admin", password: "123456", brand: "Genérico" },
  { username: "admin", password: "", brand: "Dahua/Hikvision" },
  { username: "admin", password: "admin123", brand: "TP-Link" },
  { username: "root", password: "root", brand: "Axis" },
];

export const AccessTestPanel: React.FC<AccessTestPanelProps> = ({
  selectedIP = "192.168.1.172",
  onComplete,
  onBack,
}) => {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [protocol, setProtocol] = useState("onvif");
  const [port, setPort] = useState(80);
  const [isTesting, setIsTesting] = useState(false);
  const [showDefaultCreds, setShowDefaultCreds] = useState(false);
  const [testResults, setTestResults] = useState<TestResult[]>([
    { protocol: "ONVIF", port: 80, status: "pending" },
    { protocol: "RTSP", port: 554, status: "pending" },
    { protocol: "HTTP", port: 80, status: "pending" },
  ]);
  const [selectedResult, setSelectedResult] = useState<TestResult | null>(null);

  /**
   * INTEGRACIÓN - Probar Acceso
   * 
   * TODO: Conectar con el store/servicio
   * 
   * @example
   * const handleTestAccess = async () => {
   *   const config: AccessTestConfig = {
   *     ip: selectedIP,
   *     port: port,
   *     protocol: protocol,
   *     credentials: {
   *       username: username,
   *       password: password,
   *     },
   *     tryAllProtocols: true, // Probar ONVIF, RTSP y HTTP
   *   };
   *   
   *   try {
   *     setIsTesting(true);
   *     const results = await scannerService.testCameraAccess(config);
   *     setTestResults(results);
   *     
   *     // Si hay resultados exitosos, habilitar botón de agregar cámara
   *     const successfulTests = results.filter(r => r.status === 'success');
   *     if (successfulTests.length > 0) {
   *       // Preparar datos para agregar cámara
   *     }
   *   } catch (error) {
   *     // Mostrar error
   *   } finally {
   *     setIsTesting(false);
   *   }
   * };
   */
  const handleTestAccess = () => {
    setIsTesting(true);
    // TODO: Implementar llamada al servicio
    console.log("Probando acceso con:", {
      ip: selectedIP,
      port,
      protocol,
      username,
      password: "***",
    });
    
    // Simular prueba temporal
    setTimeout(() => {
      setTestResults([
        {
          protocol: "ONVIF",
          port: 80,
          status: "success",
          message: "Conexión exitosa",
          details: {
            manufacturer: "Dahua",
            model: "IPC-HDW2431T-AS-S2",
            firmware: "V2.800.0000000.31.R",
            capabilities: ["PTZ", "Analytics", "Audio", "Events"],
          },
        },
        {
          protocol: "RTSP",
          port: 554,
          status: "success",
          message: "Stream disponible",
        },
        {
          protocol: "HTTP",
          port: 80,
          status: "failed",
          message: "Autenticación fallida",
        },
      ]);
      setIsTesting(false);
    }, 3000);
  };

  const handleSelectCredential = (cred: typeof DEFAULT_CREDENTIALS[0]) => {
    setUsername(cred.username);
    setPassword(cred.password);
    setShowDefaultCreds(false);
  };

  const getProtocolPorts = () => {
    switch (protocol) {
      case "onvif":
        return [80, 8080, 2020, 8000];
      case "rtsp":
        return [554, 8554, 5543];
      case "http":
        return [80, 8080, 8081];
      default:
        return [80];
    }
  };

  const successfulTests = testResults.filter((r) => r.status === "success");

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
          Prueba de Acceso
        </Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Dispositivo:
          </Typography>
          <Chip
            label={selectedIP}
            size="small"
            sx={{ fontFamily: "monospace" }}
          />
        </Box>
        <Typography variant="caption" color="text.secondary">
          Verifica las credenciales y establece conexión con la cámara
        </Typography>
      </Box>

      {/* Formulario de credenciales */}
      <Paper
        variant="outlined"
        sx={{
          p: 2,
          mb: 3,
        }}
      >
        <Typography variant="body2" sx={{ fontWeight: 500, mb: 2 }}>
          Credenciales de Acceso
        </Typography>

        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {/* Usuario */}
          <TextField
            fullWidth
            size="small"
            label="Usuario"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <UserIcon fontSize="small" color="action" />
                </InputAdornment>
              ),
            }}
            disabled={isTesting}
          />

          {/* Contraseña */}
          <TextField
            fullWidth
            size="small"
            label="Contraseña"
            type={showPassword ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <PasswordIcon fontSize="small" color="action" />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    size="small"
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
            disabled={isTesting}
          />

          {/* Botón para mostrar credenciales comunes */}
          <Button
            size="small"
            variant="text"
            onClick={() => setShowDefaultCreds(!showDefaultCreds)}
            endIcon={showDefaultCreds ? <ExpandLess /> : <ExpandMore />}
            sx={{ 
              alignSelf: "flex-start",
              textTransform: "none",
              color: "text.secondary",
            }}
          >
            Usar credenciales comunes
          </Button>

          <Collapse in={showDefaultCreds}>
            <Paper
              variant="outlined"
              sx={{
                p: 1,
                backgroundColor: (theme) =>
                  theme.palette.mode === "dark"
                    ? "rgba(255, 255, 255, 0.02)"
                    : "rgba(0, 0, 0, 0.01)",
              }}
            >
              <List dense>
                {DEFAULT_CREDENTIALS.map((cred, index) => (
                  <ListItem
                    key={index}
                    button
                    onClick={() => handleSelectCredential(cred)}
                    sx={{
                      borderRadius: 1,
                      "&:hover": {
                        backgroundColor: (theme) => theme.palette.action.hover,
                      },
                    }}
                  >
                    <ListItemText
                      primary={
                        <Typography variant="caption" sx={{ fontFamily: "monospace" }}>
                          {cred.username} / {cred.password || "(vacío)"}
                        </Typography>
                      }
                      secondary={
                        <Typography variant="caption" color="text.secondary">
                          {cred.brand}
                        </Typography>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Collapse>

          <Divider />

          {/* Protocolo y puerto */}
          <Box sx={{ display: "flex", gap: 2 }}>
            <FormControl size="small" sx={{ flex: 1 }}>
              <InputLabel>Protocolo</InputLabel>
              <Select
                value={protocol}
                onChange={(e) => {
                  setProtocol(e.target.value);
                  setPort(getProtocolPorts()[0]);
                }}
                disabled={isTesting}
                startAdornment={
                  <InputAdornment position="start">
                    <ProtocolIcon fontSize="small" color="action" />
                  </InputAdornment>
                }
              >
                <MenuItem value="onvif">ONVIF</MenuItem>
                <MenuItem value="rtsp">RTSP</MenuItem>
                <MenuItem value="http">HTTP/CGI</MenuItem>
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 100 }}>
              <InputLabel>Puerto</InputLabel>
              <Select
                value={port}
                onChange={(e) => setPort(Number(e.target.value))}
                disabled={isTesting}
              >
                {getProtocolPorts().map((p) => (
                  <MenuItem key={p} value={p}>
                    {p}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Box>
      </Paper>

      {/* Progreso de prueba */}
      {isTesting && (
        <Paper
          sx={{
            p: 2,
            mb: 3,
            backgroundColor: colorTokens.primary[50],
            border: `1px solid ${colorTokens.primary[200]}`,
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
            Probando conexión...
          </Typography>
          <LinearProgress
            sx={{
              height: 6,
              borderRadius: 3,
              backgroundColor: colorTokens.primary[100],
              "& .MuiLinearProgress-bar": {
                borderRadius: 3,
                backgroundColor: colorTokens.primary[500],
              },
            }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
            Verificando credenciales y estableciendo conexión con la cámara
          </Typography>
        </Paper>
      )}

      {/* Resultados de las pruebas */}
      {testResults.some((r) => r.status !== "pending") && (
        <Paper variant="outlined" sx={{ mb: 3 }}>
          <Box sx={{ p: 2, borderBottom: 1, borderColor: "divider" }}>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              Resultados de Conexión
            </Typography>
          </Box>
          <List>
            {testResults.map((result, index) => (
              <React.Fragment key={result.protocol}>
                <ListItem
                  button={result.status === "success"}
                  onClick={() => 
                    result.status === "success" && 
                    setSelectedResult(selectedResult?.protocol === result.protocol ? null : result)
                  }
                  sx={{
                    "&:hover": result.status === "success" && {
                      backgroundColor: (theme) => theme.palette.action.hover,
                    },
                  }}
                >
                  <ListItemIcon>
                    {result.status === "success" ? (
                      <SuccessIcon sx={{ color: colorTokens.status.connected }} />
                    ) : result.status === "failed" ? (
                      <ErrorIcon sx={{ color: colorTokens.status.error }} />
                    ) : result.status === "testing" ? (
                      <Box sx={{ width: 24, height: 24 }}>
                        <LinearProgress />
                      </Box>
                    ) : (
                      <Box sx={{ width: 24, height: 24, opacity: 0.3 }}>○</Box>
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {result.protocol}
                        </Typography>
                        <Chip
                          label={`Puerto ${result.port}`}
                          size="small"
                          sx={{ fontSize: "0.7rem" }}
                        />
                      </Box>
                    }
                    secondary={result.message}
                  />
                  {result.status === "success" && result.details && (
                    <IconButton size="small">
                      {selectedResult?.protocol === result.protocol ? (
                        <ExpandLess />
                      ) : (
                        <ExpandMore />
                      )}
                    </IconButton>
                  )}
                </ListItem>

                {/* Detalles expandibles */}
                {result.details && (
                  <Collapse in={selectedResult?.protocol === result.protocol}>
                    <Box sx={{ px: 9, pb: 2 }}>
                      <Paper
                        variant="outlined"
                        sx={{
                          p: 2,
                          backgroundColor: (theme) =>
                            theme.palette.mode === "dark"
                              ? "rgba(255, 255, 255, 0.02)"
                              : "rgba(0, 0, 0, 0.01)",
                        }}
                      >
                        <Typography variant="caption" color="text.secondary">
                          Información del Dispositivo:
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="body2">
                            <strong>Fabricante:</strong> {result.details.manufacturer}
                          </Typography>
                          <Typography variant="body2">
                            <strong>Modelo:</strong> {result.details.model}
                          </Typography>
                          <Typography variant="body2">
                            <strong>Firmware:</strong> {result.details.firmware}
                          </Typography>
                          {result.details.capabilities && (
                            <Box sx={{ mt: 1 }}>
                              <Typography variant="caption" color="text.secondary">
                                Capacidades:
                              </Typography>
                              <Box sx={{ display: "flex", gap: 0.5, mt: 0.5, flexWrap: "wrap" }}>
                                {result.details.capabilities.map((cap) => (
                                  <Chip
                                    key={cap}
                                    label={cap}
                                    size="small"
                                    variant="outlined"
                                    sx={{ fontSize: "0.7rem" }}
                                  />
                                ))}
                              </Box>
                            </Box>
                          )}
                        </Box>
                      </Paper>
                    </Box>
                  </Collapse>
                )}

                {index < testResults.length - 1 && (
                  <Divider variant="inset" component="li" />
                )}
              </React.Fragment>
            ))}
          </List>
        </Paper>
      )}

      {/* Alerta de éxito */}
      {successfulTests.length > 0 && !isTesting && (
        <Alert
          severity="success"
          variant="outlined"
          sx={{ mb: 3 }}
          action={
            <Button
              size="small"
              startIcon={<SaveIcon />}
              onClick={onComplete}
              sx={{ textTransform: "none" }}
            >
              Guardar y Continuar
            </Button>
          }
        >
          ¡Conexión exitosa! Se estableció comunicación con la cámara mediante{" "}
          {successfulTests.map((r) => r.protocol).join(" y ")}.
        </Alert>
      )}

      {/* Botones de acción */}
      <Box sx={{ display: "flex", gap: 2 }}>
        <Button variant="outlined" onClick={onBack}>
          Atrás
        </Button>
        {!isTesting && (
          <Button
            variant="contained"
            fullWidth
            startIcon={<TestIcon />}
            onClick={handleTestAccess}
            disabled={!username}
          >
            Probar Conexión
          </Button>
        )}
        {successfulTests.length > 0 && (
          <Tooltip title="Agregar cámara a la lista">
            <Button
              variant="contained"
              color="success"
              onClick={onComplete}
              sx={{ minWidth: 140 }}
              startIcon={<SuccessIcon />}
            >
              Agregar Cámara
            </Button>
          </Tooltip>
        )}
      </Box>
    </Box>
  );
};