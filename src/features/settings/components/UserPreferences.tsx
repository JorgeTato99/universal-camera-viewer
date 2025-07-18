/**
 * 👤 User Preferences Component - Universal Camera Viewer
 * Preferencias de usuario e interfaz
 */

import React, { memo, useState, useCallback } from "react";
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Slider,
  Button,
  Fade,
  Grow,
  RadioGroup,
  Radio,
  Divider,
  Chip,
  Alert,
} from "@mui/material";
import {
  Person as UserIcon,
  Palette as ThemeIcon,
  Language as LanguageIcon,
  ViewModule as LayoutIcon,
  Save as SaveIcon,
  RestartAlt as ResetIcon,
} from "@mui/icons-material";
import { useTheme } from "@mui/material/styles";

interface UserPreferencesConfig {
  theme: "light" | "dark" | "system";
  language: "es" | "en";
  gridColumns: number;
  autoPlayVideos: boolean;
  soundAlerts: boolean;
  notificationsEnabled: boolean;
  compactMode: boolean;
  animationsEnabled: boolean;
  debugMode: boolean;
  logLevel: "DEBUG" | "INFO" | "WARNING" | "ERROR";
}

const DEFAULT_CONFIG: UserPreferencesConfig = {
  theme: "system",
  language: "es",
  gridColumns: 3,
  autoPlayVideos: true,
  soundAlerts: true,
  notificationsEnabled: true,
  compactMode: false,
  animationsEnabled: true,
  debugMode: false,
  logLevel: "INFO",
};

export const UserPreferences = memo(() => {
  const theme = useTheme();
  const [config, setConfig] = useState<UserPreferencesConfig>(DEFAULT_CONFIG);
  const [hasChanges, setHasChanges] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleChange = useCallback((field: keyof UserPreferencesConfig, value: any) => {
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
          <UserIcon sx={{ mr: 2, color: "primary.main", fontSize: 28 }} />
          <Typography variant="h5" component="h2">
            Preferencias de Usuario
          </Typography>
        </Box>

        {/* Appearance Settings */}
        <Grow in timeout={800} style={{ transitionDelay: "100ms" }}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
              <ThemeIcon sx={{ mr: 1, color: "text.secondary" }} />
              <Typography variant="h6">Apariencia</Typography>
            </Box>

            <FormControl component="fieldset" sx={{ mb: 3 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Tema de la Aplicación
              </Typography>
              <RadioGroup
                row
                value={config.theme}
                onChange={(e) => handleChange("theme", e.target.value)}
              >
                <FormControlLabel 
                  value="light" 
                  control={<Radio />} 
                  label={
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <Box
                        sx={{
                          width: 20,
                          height: 20,
                          borderRadius: "50%",
                          backgroundColor: "#ffffff",
                          border: "2px solid #e0e0e0",
                        }}
                      />
                      Claro
                    </Box>
                  }
                />
                <FormControlLabel 
                  value="dark" 
                  control={<Radio />} 
                  label={
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <Box
                        sx={{
                          width: 20,
                          height: 20,
                          borderRadius: "50%",
                          backgroundColor: "#121212",
                          border: "2px solid #424242",
                        }}
                      />
                      Oscuro
                    </Box>
                  }
                />
                <FormControlLabel 
                  value="system" 
                  control={<Radio />} 
                  label="Sistema" 
                />
              </RadioGroup>
            </FormControl>

            <Divider sx={{ my: 2 }} />

            <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={config.compactMode}
                    onChange={(e) => handleChange("compactMode", e.target.checked)}
                  />
                }
                label="Modo Compacto"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={config.animationsEnabled}
                    onChange={(e) => handleChange("animationsEnabled", e.target.checked)}
                  />
                }
                label="Animaciones"
              />
            </Box>
          </Paper>
        </Grow>

        {/* Language and Region */}
        <Grow in timeout={800} style={{ transitionDelay: "200ms" }}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
              <LanguageIcon sx={{ mr: 1, color: "text.secondary" }} />
              <Typography variant="h6">Idioma y Región</Typography>
            </Box>

            <FormControl fullWidth sx={{ maxWidth: 300 }}>
              <InputLabel>Idioma</InputLabel>
              <Select
                value={config.language}
                onChange={(e) => handleChange("language", e.target.value)}
                label="Idioma"
              >
                <MenuItem value="es">
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Box component="span" sx={{ fontSize: 20 }}>🇪🇸</Box>
                    Español
                  </Box>
                </MenuItem>
                <MenuItem value="en">
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Box component="span" sx={{ fontSize: 20 }}>🇺🇸</Box>
                    English
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>
          </Paper>
        </Grow>

        {/* Layout Preferences */}
        <Grow in timeout={800} style={{ transitionDelay: "300ms" }}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
              <LayoutIcon sx={{ mr: 1, color: "text.secondary" }} />
              <Typography variant="h6">Diseño</Typography>
            </Box>

            <Box sx={{ mb: 3 }}>
              <Typography variant="body1" gutterBottom>
                Columnas de Grid por Defecto: {config.gridColumns}
              </Typography>
              <Slider
                value={config.gridColumns}
                onChange={(_, value) => handleChange("gridColumns", value as number)}
                min={1}
                max={6}
                marks={[
                  { value: 1, label: "1" },
                  { value: 2, label: "2" },
                  { value: 3, label: "3" },
                  { value: 4, label: "4" },
                  { value: 5, label: "5" },
                  { value: 6, label: "6" },
                ]}
                valueLabelDisplay="auto"
                sx={{ maxWidth: 400 }}
              />
            </Box>
          </Paper>
        </Grow>

        {/* Behavior Settings */}
        <Grow in timeout={800} style={{ transitionDelay: "400ms" }}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Comportamiento
            </Typography>

            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={config.autoPlayVideos}
                    onChange={(e) => handleChange("autoPlayVideos", e.target.checked)}
                  />
                }
                label="Reproducir Videos Automáticamente"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={config.soundAlerts}
                    onChange={(e) => handleChange("soundAlerts", e.target.checked)}
                  />
                }
                label="Alertas Sonoras"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={config.notificationsEnabled}
                    onChange={(e) => handleChange("notificationsEnabled", e.target.checked)}
                  />
                }
                label="Notificaciones del Sistema"
              />
            </Box>
          </Paper>
        </Grow>

        {/* Developer Settings */}
        <Grow in timeout={800} style={{ transitionDelay: "500ms" }}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Opciones de Desarrollador
            </Typography>

            <FormControlLabel
              control={
                <Switch
                  checked={config.debugMode}
                  onChange={(e) => handleChange("debugMode", e.target.checked)}
                  color="warning"
                />
              }
              label="Modo Debug"
              sx={{ mb: 2 }}
            />

            {config.debugMode && (
              <Fade in>
                <FormControl fullWidth sx={{ maxWidth: 300 }}>
                  <InputLabel>Nivel de Log</InputLabel>
                  <Select
                    value={config.logLevel}
                    onChange={(e) => handleChange("logLevel", e.target.value)}
                    label="Nivel de Log"
                  >
                    <MenuItem value="DEBUG">
                      <Chip label="DEBUG" size="small" color="info" />
                    </MenuItem>
                    <MenuItem value="INFO">
                      <Chip label="INFO" size="small" color="success" />
                    </MenuItem>
                    <MenuItem value="WARNING">
                      <Chip label="WARNING" size="small" color="warning" />
                    </MenuItem>
                    <MenuItem value="ERROR">
                      <Chip label="ERROR" size="small" color="error" />
                    </MenuItem>
                  </Select>
                </FormControl>
              </Fade>
            )}
          </Paper>
        </Grow>

        {/* Actions */}
        <Fade in timeout={800} style={{ transitionDelay: "600ms" }}>
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

        {/* Theme Preview Alert */}
        {config.theme !== DEFAULT_CONFIG.theme && (
          <Fade in>
            <Alert severity="info" sx={{ mt: 2 }}>
              El cambio de tema se aplicará inmediatamente después de guardar.
            </Alert>
          </Fade>
        )}
      </Box>
    </Fade>
  );
});

UserPreferences.displayName = "UserPreferences";

export default UserPreferences;