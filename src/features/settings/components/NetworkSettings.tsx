/**
 * ⚙️ Network Settings Component - Universal Camera Viewer
 * Configuración de red y conectividad del sistema
 */

import React, { memo, useState, useCallback } from "react";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Slider,
  Switch,
  FormControlLabel,
  FormGroup,
  Divider,
  Button,
  InputAdornment,
  Fade,
  Grow,
  Alert,
  Tooltip,
  IconButton,
} from "@mui/material";
import {
  Save as SaveIcon,
  RestartAlt as ResetIcon,
  Info as InfoIcon,
  NetworkCheck as NetworkIcon,
} from "@mui/icons-material";

interface NetworkConfig {
  connectionTimeout: number;
  maxRetries: number;
  retryDelay: number;
  scanTimeout: number;
  concurrentConnections: number;
  bufferSize: number;
  autoReconnect: boolean;
  reconnectInterval: number;
}

const DEFAULT_CONFIG: NetworkConfig = {
  connectionTimeout: 10,
  maxRetries: 3,
  retryDelay: 1.0,
  scanTimeout: 5,
  concurrentConnections: 4,
  bufferSize: 1,
  autoReconnect: true,
  reconnectInterval: 5,
};

export const NetworkSettings = memo(() => {
  const [config, setConfig] = useState<NetworkConfig>(DEFAULT_CONFIG);
  const [hasChanges, setHasChanges] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleChange = useCallback((field: keyof NetworkConfig, value: any) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
    setHasChanges(true);
  }, []);

  const handleSave = useCallback(async () => {
    setSaving(true);
    // TODO: Implementar guardado real con API
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setSaving(false);
    setHasChanges(false);
  }, [config]);

  const handleReset = useCallback(() => {
    setConfig(DEFAULT_CONFIG);
    setHasChanges(false);
  }, []);

  return (
    <Fade in timeout={600}>
      <Box>
        {/* Header */}
        <Box sx={{ display: "flex", alignItems: "center", mb: 3 }}>
          <NetworkIcon sx={{ mr: 2, color: "primary.main", fontSize: 28 }} />
          <Typography variant="h5" component="h2">
            Configuración de Red
          </Typography>
        </Box>

        {/* Timeouts Section */}
        <Grow in timeout={800} style={{ transitionDelay: "100ms" }}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Tiempos de Espera
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Configura los tiempos de espera para las operaciones de red
            </Typography>

            <Box sx={{ mt: 3 }}>
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                  <Typography variant="body1">
                    Timeout de Conexión: {config.connectionTimeout}s
                  </Typography>
                  <Tooltip title="Tiempo máximo para establecer conexión con una cámara">
                    <IconButton size="small" sx={{ ml: 1 }}>
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
                <Slider
                  value={config.connectionTimeout}
                  onChange={(_, value) =>
                    handleChange("connectionTimeout", value as number)
                  }
                  min={1}
                  max={30}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>

              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                  <Typography variant="body1">
                    Timeout de Escaneo: {config.scanTimeout}s
                  </Typography>
                  <Tooltip title="Tiempo máximo para escanear un dispositivo">
                    <IconButton size="small" sx={{ ml: 1 }}>
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
                <Slider
                  value={config.scanTimeout}
                  onChange={(_, value) =>
                    handleChange("scanTimeout", value as number)
                  }
                  min={1}
                  max={30}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>
            </Box>
          </Paper>
        </Grow>

        {/* Retry Configuration */}
        <Grow in timeout={800} style={{ transitionDelay: "200ms" }}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Configuración de Reintentos
            </Typography>

            <Box sx={{ display: "flex", gap: 3, flexWrap: "wrap", mt: 2 }}>
              <TextField
                label="Máximo de Reintentos"
                type="number"
                value={config.maxRetries}
                onChange={(e) =>
                  handleChange("maxRetries", parseInt(e.target.value) || 0)
                }
                InputProps={{
                  inputProps: { min: 1, max: 10 },
                  endAdornment: (
                    <InputAdornment position="end">intentos</InputAdornment>
                  ),
                }}
                sx={{ minWidth: 200 }}
              />

              <TextField
                label="Delay entre Reintentos"
                type="number"
                value={config.retryDelay}
                onChange={(e) =>
                  handleChange("retryDelay", parseFloat(e.target.value) || 0)
                }
                InputProps={{
                  inputProps: { min: 0.5, max: 5.0, step: 0.5 },
                  endAdornment: (
                    <InputAdornment position="end">segundos</InputAdornment>
                  ),
                }}
                sx={{ minWidth: 200 }}
              />
            </Box>

            <Divider sx={{ my: 3 }} />

            <FormGroup>
              <FormControlLabel
                control={
                  <Switch
                    checked={config.autoReconnect}
                    onChange={(e) =>
                      handleChange("autoReconnect", e.target.checked)
                    }
                  />
                }
                label="Reconexión Automática"
              />
              {config.autoReconnect && (
                <Fade in>
                  <TextField
                    label="Intervalo de Reconexión"
                    type="number"
                    value={config.reconnectInterval}
                    onChange={(e) =>
                      handleChange(
                        "reconnectInterval",
                        parseInt(e.target.value) || 0
                      )
                    }
                    InputProps={{
                      inputProps: { min: 1, max: 60 },
                      endAdornment: (
                        <InputAdornment position="end">segundos</InputAdornment>
                      ),
                    }}
                    sx={{ mt: 2, maxWidth: 300 }}
                  />
                </Fade>
              )}
            </FormGroup>
          </Paper>
        </Grow>

        {/* Performance Settings */}
        <Grow in timeout={800} style={{ transitionDelay: "300ms" }}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Rendimiento
            </Typography>

            <Box sx={{ mt: 2 }}>
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                  <Typography variant="body1">
                    Conexiones Concurrentes: {config.concurrentConnections}
                  </Typography>
                  <Tooltip title="Número máximo de conexiones simultáneas">
                    <IconButton size="small" sx={{ ml: 1 }}>
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
                <Slider
                  value={config.concurrentConnections}
                  onChange={(_, value) =>
                    handleChange("concurrentConnections", value as number)
                  }
                  min={1}
                  max={16}
                  marks={[
                    { value: 1, label: "1" },
                    { value: 4, label: "4" },
                    { value: 8, label: "8" },
                    { value: 12, label: "12" },
                    { value: 16, label: "16" },
                  ]}
                  valueLabelDisplay="auto"
                />
              </Box>

              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                  <Typography variant="body1">
                    Tamaño del Buffer: {config.bufferSize} frames
                  </Typography>
                  <Tooltip title="Número de frames en buffer para streaming">
                    <IconButton size="small" sx={{ ml: 1 }}>
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
                <Slider
                  value={config.bufferSize}
                  onChange={(_, value) =>
                    handleChange("bufferSize", value as number)
                  }
                  min={1}
                  max={10}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>
            </Box>
          </Paper>
        </Grow>

        {/* Actions */}
        <Fade in timeout={800} style={{ transitionDelay: "400ms" }}>
          <Box sx={{ display: "flex", gap: 2, justifyContent: "flex-end" }}>
            <Button
              variant="outlined"
              startIcon={<ResetIcon />}
              onClick={handleReset}
              disabled={!hasChanges}
            >
              Restablecer
            </Button>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSave}
              disabled={!hasChanges || saving}
            >
              {saving ? "Guardando..." : "Guardar Cambios"}
            </Button>
          </Box>
        </Fade>

        {/* Info Alert */}
        {hasChanges && (
          <Fade in>
            <Alert severity="info" sx={{ mt: 2 }}>
              Los cambios se aplicarán después de guardar la configuración.
            </Alert>
          </Fade>
        )}
      </Box>
    </Fade>
  );
});

NetworkSettings.displayName = "NetworkSettings";

export default NetworkSettings;