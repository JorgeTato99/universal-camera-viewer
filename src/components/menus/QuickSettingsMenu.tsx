/**
 * 🎯 Quick Settings Menu - Universal Camera Viewer
 * Menú desplegable de configuración rápida en el TopBar
 */

import React, { useState } from "react";
import {
  Popover,
  Box,
  Typography,
  IconButton,
  Divider,
  Slider,
  Switch,
  Select,
  MenuItem,
  FormControl,
  Button,
  Tooltip,
  Paper,
  alpha,
  Fade,
  Zoom,
  useTheme,
  SelectChangeEvent,
} from "@mui/material";
import {
  Settings as SettingsIcon,
  VolumeUp as VolumeIcon,
  Videocam as QualityIcon,
  Notifications as NotificationIcon,
  Language as LanguageIcon,
  FolderOpen as FolderIcon,
  ArrowForward as ArrowIcon,
  Close as CloseIcon,
} from "@mui/icons-material";
import { colorTokens, borderTokens, spacingTokens } from "../../design-system/tokens";

interface QuickSettingsMenuProps {
  anchorEl: HTMLElement | null;
  open: boolean;
  onClose: () => void;
}

// Configuración temporal (luego vendrá del store)
interface QuickSettings {
  alertVolume: number;
  streamQuality: "auto" | "hd" | "sd";
  notifications: boolean;
  language: "es" | "en";
}

export const QuickSettingsMenu: React.FC<QuickSettingsMenuProps> = ({
  anchorEl,
  open,
  onClose,
}) => {
  const theme = useTheme();
  const [settings, setSettings] = useState<QuickSettings>({
    alertVolume: 75,
    streamQuality: "auto",
    notifications: true,
    language: "es",
  });

  /**
   * 🚀 INTEGRACIÓN PENDIENTE - Sistema de Configuración Rápida
   * 
   * TODO: Conectar todos los controles con el store de configuración y backend
   * 
   * ARQUITECTURA SUGERIDA:
   * 1. Store Zustand: useSettingsStore para estado global
   * 2. Servicio: settingsService.updateQuickSettings()
   * 3. WebSocket: Sincronizar cambios entre pestañas/dispositivos
   * 
   * ENDPOINTS BACKEND:
   * - GET /api/v2/settings/quick - Obtener configuración actual
   * - PUT /api/v2/settings/quick - Actualizar configuración
   * - WS evento: 'settings:updated' - Notificar cambios
   */
  const handleVolumeChange = (_: Event, value: number | number[]) => {
    setSettings({ ...settings, alertVolume: value as number });
    /**
     * TODO: Implementar persistencia y prueba de sonido
     * ```typescript
     * const volume = value as number;
     * useSettingsStore.setState({ alertVolume: volume });
     * const audio = new Audio('/sounds/alert-test.mp3');
     * audio.volume = volume / 100;
     * audio.play();
     * ```
     */
    console.log("🔧 MOCK: Volumen de alertas:", value);
  };

  const handleQualityChange = (event: SelectChangeEvent) => {
    setSettings({ ...settings, streamQuality: event.target.value as any });
    /**
     * TODO: Aplicar calidad a streams activos
     * ```typescript
     * const quality = event.target.value;
     * useSettingsStore.setState({ streamQuality: quality });
     * streamService.updateAllStreamsQuality(quality);
     * ```
     */
    console.log("🔧 MOCK: Calidad de streaming:", event.target.value);
  };

  const handleNotificationsToggle = () => {
    setSettings({ ...settings, notifications: !settings.notifications });
    /**
     * TODO: Configurar permisos de notificaciones
     * ```typescript
     * if (!settings.notifications && Notification.permission === 'default') {
     *   await Notification.requestPermission();
     * }
     * useSettingsStore.setState({ notifications: !settings.notifications });
     * ```
     */
    console.log("🔧 MOCK: Notificaciones:", !settings.notifications);
  };

  const handleLanguageChange = (event: SelectChangeEvent) => {
    setSettings({ ...settings, language: event.target.value as any });
    /**
     * TODO: Sistema de internacionalización (i18n)
     * ```typescript
     * import { useTranslation } from 'react-i18next';
     * const { i18n } = useTranslation();
     * await i18n.changeLanguage(event.target.value);
     * localStorage.setItem('language', event.target.value);
     * ```
     * REQUIERE: yarn add react-i18next i18next
     */
    console.log("🔧 MOCK: Idioma:", event.target.value);
  };

  const handleOpenRecordingsFolder = () => {
    /**
     * TODO: Abrir carpeta con Tauri
     * ```typescript
     * import { open } from '@tauri-apps/api/shell';
     * const recordingsPath = await settingsService.getRecordingsPath();
     * await open(recordingsPath);
     * ```
     * REQUIERE: Permisos en tauri.conf.json
     */
    console.log("🔧 MOCK: Abrir carpeta de grabaciones - REQUIERE TAURI");
  };

  const handleOpenFullSettings = () => {
    /**
     * TODO: Navegar a configuración completa
     * ```typescript
     * import { useNavigate } from 'react-router-dom';
     * const navigate = useNavigate();
     * navigate('/settings');
     * ```
     */
    console.log("🔧 MOCK: Navegar a configuración completa");
    onClose();
  };

  const getVolumeIcon = () => {
    if (settings.alertVolume === 0) return "🔇";
    if (settings.alertVolume < 30) return "🔈";
    if (settings.alertVolume < 70) return "🔉";
    return "🔊";
  };

  return (
    <Popover
      open={open}
      anchorEl={anchorEl}
      onClose={onClose}
      anchorOrigin={{
        vertical: "bottom",
        horizontal: "right",
      }}
      transformOrigin={{
        vertical: "top",
        horizontal: "right",
      }}
      TransitionComponent={Zoom}
      TransitionProps={{
        timeout: 300,
      }}
      PaperProps={{
        sx: {
          width: 320,
          maxHeight: 500,
          borderRadius: borderTokens.radius.lg,
          boxShadow: theme.shadows[8],
          border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          overflow: "hidden",
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2,
          pb: 1.5,
          background: theme.palette.mode === "dark"
            ? `linear-gradient(135deg, ${alpha(colorTokens.primary[900], 0.2)} 0%, ${alpha(colorTokens.primary[800], 0.1)} 100%)`
            : `linear-gradient(135deg, ${alpha(colorTokens.primary[50], 0.8)} 0%, ${alpha(colorTokens.primary[100], 0.4)} 100%)`,
          borderBottom: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <SettingsIcon 
              sx={{ 
                fontSize: 20, 
                color: colorTokens.primary[500],
              }} 
            />
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              Configuración Rápida
            </Typography>
          </Box>
          <Tooltip title="Cerrar" arrow placement="left">
            <IconButton
              size="small"
              onClick={onClose}
              sx={{
                opacity: 0.7,
                transition: "all 0.3s ease",
                "&:hover": {
                  opacity: 1,
                  backgroundColor: alpha(theme.palette.action.hover, 0.5),
                },
              }}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Box sx={{ p: 2 }}>
        {/* Volumen de Alertas */}
        <Fade in timeout={400}>
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
              <VolumeIcon 
                sx={{ 
                  fontSize: 20, 
                  color: theme.palette.text.secondary,
                  transition: "color 0.3s ease",
                }} 
              />
              <Typography variant="body2" sx={{ fontWeight: 500, flex: 1 }}>
                Volumen de Alertas
              </Typography>
              <Typography 
                variant="caption" 
                sx={{ 
                  fontWeight: 600,
                  color: colorTokens.primary[500],
                  minWidth: 35,
                  textAlign: "right",
                }}
              >
                {settings.alertVolume}%
              </Typography>
            </Box>
            <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
              <Typography variant="caption" sx={{ fontSize: 18 }}>
                {getVolumeIcon()}
              </Typography>
              <Slider
                value={settings.alertVolume}
                onChange={handleVolumeChange}
                aria-label="Volumen de alertas"
                sx={{
                  color: colorTokens.primary[500],
                  "& .MuiSlider-thumb": {
                    width: 16,
                    height: 16,
                    transition: "all 0.3s ease",
                    "&:hover": {
                      boxShadow: `0 0 0 8px ${alpha(colorTokens.primary[500], 0.16)}`,
                    },
                  },
                  "& .MuiSlider-track": {
                    height: 4,
                  },
                  "& .MuiSlider-rail": {
                    height: 4,
                    opacity: 0.3,
                  },
                }}
              />
            </Box>
          </Box>
        </Fade>

        <Divider sx={{ my: 2 }} />

        {/* Calidad de Streaming */}
        <Fade in timeout={500}>
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
              <QualityIcon 
                sx={{ 
                  fontSize: 20, 
                  color: theme.palette.text.secondary,
                }} 
              />
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                Calidad de Streaming
              </Typography>
            </Box>
            <FormControl size="small" fullWidth>
              <Select
                value={settings.streamQuality}
                onChange={handleQualityChange}
                sx={{
                  "& .MuiOutlinedInput-notchedOutline": {
                    borderRadius: borderTokens.radius.md,
                  },
                }}
              >
                <MenuItem value="auto">
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Typography variant="body2">Automático</Typography>
                    <Typography variant="caption" color="text.secondary">
                      (Recomendado)
                    </Typography>
                  </Box>
                </MenuItem>
                <MenuItem value="hd">
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Typography variant="body2">Alta Definición</Typography>
                    <Typography variant="caption" color="text.secondary">
                      1080p
                    </Typography>
                  </Box>
                </MenuItem>
                <MenuItem value="sd">
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Typography variant="body2">Definición Estándar</Typography>
                    <Typography variant="caption" color="text.secondary">
                      480p
                    </Typography>
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Fade>

        <Divider sx={{ my: 2 }} />

        {/* Notificaciones */}
        <Fade in timeout={600}>
          <Box 
            sx={{ 
              mb: 3,
              p: 1.5,
              borderRadius: borderTokens.radius.md,
              backgroundColor: settings.notifications
                ? alpha(colorTokens.status.connected, 0.05)
                : "transparent",
              border: `1px solid ${settings.notifications
                ? alpha(colorTokens.status.connected, 0.2)
                : "transparent"
              }`,
              transition: "all 0.3s ease",
              cursor: "pointer",
              "&:hover": {
                backgroundColor: alpha(
                  settings.notifications 
                    ? colorTokens.status.connected 
                    : theme.palette.action.hover, 
                  0.08
                ),
              },
            }}
            onClick={handleNotificationsToggle}
          >
            <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <NotificationIcon 
                  sx={{ 
                    fontSize: 20, 
                    color: settings.notifications 
                      ? colorTokens.status.connected 
                      : theme.palette.text.secondary,
                    transition: "color 0.3s ease",
                  }} 
                />
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    Notificaciones
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {settings.notifications ? "Activadas" : "Desactivadas"}
                  </Typography>
                </Box>
              </Box>
              <Switch
                checked={settings.notifications}
                onChange={handleNotificationsToggle}
                size="small"
                sx={{
                  "& .MuiSwitch-switchBase.Mui-checked": {
                    color: colorTokens.status.connected,
                  },
                  "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": {
                    backgroundColor: colorTokens.status.connected,
                  },
                }}
              />
            </Box>
          </Box>
        </Fade>

        <Divider sx={{ my: 2 }} />

        {/* Idioma */}
        <Fade in timeout={700}>
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
              <LanguageIcon 
                sx={{ 
                  fontSize: 20, 
                  color: theme.palette.text.secondary,
                }} 
              />
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                Idioma
              </Typography>
            </Box>
            <FormControl size="small" fullWidth>
              <Select
                value={settings.language}
                onChange={handleLanguageChange}
                sx={{
                  "& .MuiOutlinedInput-notchedOutline": {
                    borderRadius: borderTokens.radius.md,
                  },
                }}
              >
                <MenuItem value="es">
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Typography variant="body2">🇪🇸</Typography>
                    <Typography variant="body2">Español</Typography>
                  </Box>
                </MenuItem>
                <MenuItem value="en">
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Typography variant="body2">🇺🇸</Typography>
                    <Typography variant="body2">English</Typography>
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Fade>

        <Divider sx={{ my: 2 }} />

        {/* Carpeta de Grabaciones */}
        <Fade in timeout={800}>
          <Box>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<FolderIcon />}
              onClick={handleOpenRecordingsFolder}
              sx={{
                justifyContent: "flex-start",
                textTransform: "none",
                borderRadius: borderTokens.radius.md,
                borderColor: theme.palette.divider,
                color: theme.palette.text.primary,
                transition: "all 0.3s ease",
                "&:hover": {
                  borderColor: colorTokens.primary[500],
                  backgroundColor: alpha(colorTokens.primary[500], 0.05),
                },
              }}
            >
              <Box sx={{ flex: 1, textAlign: "left" }}>
                <Typography variant="body2">
                  Carpeta de Grabaciones
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  C:\Recordings\UniversalCameraViewer
                </Typography>
              </Box>
            </Button>
          </Box>
        </Fade>
      </Box>

      {/* Footer */}
      <Fade in timeout={900}>
        <Box
          sx={{
            p: 2,
            pt: 1,
            borderTop: `1px solid ${theme.palette.divider}`,
            backgroundColor: theme.palette.mode === "dark"
              ? alpha(theme.palette.background.paper, 0.5)
              : alpha(theme.palette.background.default, 0.8),
          }}
        >
          <Button
            fullWidth
            size="small"
            endIcon={<ArrowIcon />}
            onClick={handleOpenFullSettings}
            sx={{
              textTransform: "none",
              justifyContent: "space-between",
              color: colorTokens.primary[500],
              transition: "all 0.3s ease",
              "&:hover": {
                backgroundColor: alpha(colorTokens.primary[500], 0.08),
                "& .MuiButton-endIcon": {
                  transform: "translateX(4px)",
                },
              },
            }}
          >
            Ver todas las configuraciones
          </Button>
        </Box>
      </Fade>
    </Popover>
  );
};