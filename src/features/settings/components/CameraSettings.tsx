/**
 * 📹 Camera Settings Component - Universal Camera Viewer
 * Configuración global de cámaras y protocolos
 */

import React, { memo, useState, useCallback } from "react";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
  Button,
  Fade,
  Grow,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  InputAdornment,
  Alert,
} from "@mui/material";
import {
  Videocam as CameraIcon,
  ExpandMore as ExpandIcon,
  Save as SaveIcon,
  RestartAlt as ResetIcon,
} from "@mui/icons-material";

interface BrandPaths {
  dahua: string;
  tplink: string;
  steren: string;
  hikvision: string;
  generic: string;
}

interface CameraConfig {
  defaultQuality: "low" | "medium" | "high";
  defaultFPS: number;
  streamBufferSize: number;
  showFPSOverlay: boolean;
  showTimestamp: boolean;
  fullscreenOnDoubleClick: boolean;
  autoResize: boolean;
  rtspPort: number;
  onvifPort: number;
  httpPort: number;
  rtspPaths: BrandPaths;
}

const DEFAULT_CONFIG: CameraConfig = {
  defaultQuality: "high",
  defaultFPS: 30,
  streamBufferSize: 10,
  showFPSOverlay: true,
  showTimestamp: false,
  fullscreenOnDoubleClick: true,
  autoResize: true,
  rtspPort: 554,
  onvifPort: 80,
  httpPort: 80,
  rtspPaths: {
    dahua: "/cam/realmonitor?channel=1&subtype=0",
    tplink: "/stream1",
    steren: "/Streaming/Channels/101",
    hikvision: "/Streaming/Channels/101",
    generic: "/stream1",
  },
};

const CAMERA_BRANDS = [
  { id: "dahua", name: "Dahua", color: "#FF6B6B" },
  { id: "tplink", name: "TP-Link", color: "#4ECDC4" },
  { id: "steren", name: "Steren", color: "#45B7D1" },
  { id: "hikvision", name: "Hikvision", color: "#96CEB4" },
  { id: "generic", name: "Genérico", color: "#95A5A6" },
];

export const CameraSettings = memo(() => {
  const [config, setConfig] = useState<CameraConfig>(DEFAULT_CONFIG);
  const [hasChanges, setHasChanges] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleChange = useCallback((field: keyof CameraConfig, value: any) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
    setHasChanges(true);
  }, []);

  const handlePathChange = useCallback((brand: keyof BrandPaths, path: string) => {
    setConfig((prev) => ({
      ...prev,
      rtspPaths: {
        ...prev.rtspPaths,
        [brand]: path,
      },
    }));
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
          <CameraIcon sx={{ mr: 2, color: "primary.main", fontSize: 28 }} />
          <Typography variant="h5" component="h2">
            Configuración de Cámaras
          </Typography>
        </Box>

        {/* Stream Settings */}
        <Grow in timeout={800} style={{ transitionDelay: "100ms" }}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Configuración de Streaming
            </Typography>

            <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 3, mt: 2 }}>
              <FormControl fullWidth>
                <InputLabel>Calidad por Defecto</InputLabel>
                <Select
                  value={config.defaultQuality}
                  onChange={(e) =>
                    handleChange("defaultQuality", e.target.value)
                  }
                  label="Calidad por Defecto"
                >
                  <MenuItem value="low">Baja (480p)</MenuItem>
                  <MenuItem value="medium">Media (720p)</MenuItem>
                  <MenuItem value="high">Alta (1080p)</MenuItem>
                </Select>
              </FormControl>

              <TextField
                label="FPS por Defecto"
                type="number"
                value={config.defaultFPS}
                onChange={(e) =>
                  handleChange("defaultFPS", parseInt(e.target.value) || 0)
                }
                InputProps={{
                  inputProps: { min: 1, max: 60 },
                  endAdornment: (
                    <InputAdornment position="end">fps</InputAdornment>
                  ),
                }}
              />

              <TextField
                label="Buffer de Stream"
                type="number"
                value={config.streamBufferSize}
                onChange={(e) =>
                  handleChange("streamBufferSize", parseInt(e.target.value) || 0)
                }
                InputProps={{
                  inputProps: { min: 1, max: 100 },
                  endAdornment: (
                    <InputAdornment position="end">frames</InputAdornment>
                  ),
                }}
              />
            </Box>

            <Divider sx={{ my: 3 }} />

            <Typography variant="subtitle1" gutterBottom>
              Opciones de Visualización
            </Typography>
            <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2, mt: 2 }}>
              <Chip
                label="Mostrar FPS"
                color={config.showFPSOverlay ? "primary" : "default"}
                onClick={() => handleChange("showFPSOverlay", !config.showFPSOverlay)}
                clickable
              />
              <Chip
                label="Mostrar Timestamp"
                color={config.showTimestamp ? "primary" : "default"}
                onClick={() => handleChange("showTimestamp", !config.showTimestamp)}
                clickable
              />
              <Chip
                label="Pantalla Completa con Doble Click"
                color={config.fullscreenOnDoubleClick ? "primary" : "default"}
                onClick={() =>
                  handleChange("fullscreenOnDoubleClick", !config.fullscreenOnDoubleClick)
                }
                clickable
              />
              <Chip
                label="Auto Ajustar Tamaño"
                color={config.autoResize ? "primary" : "default"}
                onClick={() => handleChange("autoResize", !config.autoResize)}
                clickable
              />
            </Box>
          </Paper>
        </Grow>

        {/* Protocol Ports */}
        <Grow in timeout={800} style={{ transitionDelay: "200ms" }}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Puertos de Protocolo
            </Typography>

            <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 2, mt: 2 }}>
              <TextField
                label="Puerto RTSP"
                type="number"
                value={config.rtspPort}
                onChange={(e) =>
                  handleChange("rtspPort", parseInt(e.target.value) || 0)
                }
                InputProps={{
                  inputProps: { min: 1, max: 65535 },
                }}
              />
              <TextField
                label="Puerto ONVIF"
                type="number"
                value={config.onvifPort}
                onChange={(e) =>
                  handleChange("onvifPort", parseInt(e.target.value) || 0)
                }
                InputProps={{
                  inputProps: { min: 1, max: 65535 },
                }}
              />
              <TextField
                label="Puerto HTTP"
                type="number"
                value={config.httpPort}
                onChange={(e) =>
                  handleChange("httpPort", parseInt(e.target.value) || 0)
                }
                InputProps={{
                  inputProps: { min: 1, max: 65535 },
                }}
              />
            </Box>
          </Paper>
        </Grow>

        {/* RTSP Paths by Brand */}
        <Grow in timeout={800} style={{ transitionDelay: "300ms" }}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Rutas RTSP por Marca
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Configura las rutas RTSP predeterminadas para cada marca de cámara
            </Typography>

            {CAMERA_BRANDS.map((brand, index) => (
              <Accordion key={brand.id}>
                <AccordionSummary expandIcon={<ExpandIcon />}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                    <Box
                      sx={{
                        width: 12,
                        height: 12,
                        borderRadius: "50%",
                        backgroundColor: brand.color,
                      }}
                    />
                    <Typography>{brand.name}</Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <TextField
                    fullWidth
                    label={`Ruta RTSP para ${brand.name}`}
                    value={config.rtspPaths[brand.id as keyof BrandPaths]}
                    onChange={(e) =>
                      handlePathChange(brand.id as keyof BrandPaths, e.target.value)
                    }
                    helperText="Ruta relativa después de rtsp://IP:PORT"
                  />
                </AccordionDetails>
              </Accordion>
            ))}
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
        <Fade in timeout={800} style={{ transitionDelay: "500ms" }}>
          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              Estas configuraciones se aplicarán como valores predeterminados para
              todas las nuevas cámaras. Las cámaras existentes mantendrán su
              configuración individual.
            </Typography>
          </Alert>
        </Fade>
      </Box>
    </Fade>
  );
});

CameraSettings.displayName = "CameraSettings";

export default CameraSettings;