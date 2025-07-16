/**
 * 🎯 About Dialog Component - Universal Camera Viewer
 * Dialog de información sobre la aplicación
 */

import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  Box,
  Typography,
  IconButton,
  Divider,
  Chip,
  Link,
  useTheme,
  alpha,
  Fade,
  Zoom,
  Tooltip,
  keyframes,
  Skeleton,
  Grow,
  Tabs,
  Tab,
  Button,
  Alert,
  CircularProgress,
  Badge,
  Paper,
} from "@mui/material";
import {
  Close as CloseIcon,
  GitHub as GitHubIcon,
  Language as WebIcon,
  Email as EmailIcon,
  Security as SecurityIcon,
  Speed as PerformanceIcon,
  Videocam as CameraIcon,
  AutoAwesome as SparkleIcon,
  Info as InfoIcon,
  Update as UpdateIcon,
  Gavel as LicenseIcon,
  CheckCircle as CheckIcon,
  Download as DownloadIcon,
  OpenInNew as OpenIcon,
} from "@mui/icons-material";
import {
  colorTokens,
  borderTokens,
  spacingTokens,
} from "../../design-system/tokens";
import { LicenseDialog } from "./LicenseDialog";

interface AboutDialogProps {
  open: boolean;
  onClose: () => void;
}

// Animaciones personalizadas
const pulseAnimation = keyframes`
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.4);
  }
  70% {
    transform: scale(1.05);
    box-shadow: 0 0 0 10px rgba(255, 255, 255, 0);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(255, 255, 255, 0);
  }
`;

const fadeInUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const slideInRight = keyframes`
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
`;

const rippleEffect = keyframes`
  0% {
    transform: scale(0);
    opacity: 1;
  }
  100% {
    transform: scale(4);
    opacity: 0;
  }
`;

const shimmer = keyframes`
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
`;

const floatAnimation = keyframes`
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
`;

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`about-tabpanel-${index}`}
      aria-labelledby={`about-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Fade in timeout={500}>
          <Box>{children}</Box>
        </Fade>
      )}
    </div>
  );
}

export const AboutDialog: React.FC<AboutDialogProps> = ({ open, onClose }) => {
  const theme = useTheme();
  const [contentLoaded, setContentLoaded] = React.useState(false);
  const [rippleActive, setRippleActive] = React.useState(false);
  const [currentTab, setCurrentTab] = useState(0);
  const [checkingUpdates, setCheckingUpdates] = useState(false);
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [currentVersion] = useState("0.9.6");
  const [latestVersion, setLatestVersion] = useState("0.9.6");
  const [licenseDialogOpen, setLicenseDialogOpen] = useState(false);

  React.useEffect(() => {
    if (open) {
      // Simular carga de contenido
      const timer = setTimeout(() => setContentLoaded(true), 300);
      return () => clearTimeout(timer);
    } else {
      setContentLoaded(false);
      setCurrentTab(0); // Reset al tab inicial
    }
  }, [open]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  /**
   * 🚀 INTEGRACIÓN PENDIENTE - Sistema de Actualizaciones
   * 
   * TODO: Conectar con servicio real de actualizaciones
   * 
   * BACKEND REQUERIDO:
   * - Endpoint: GET /api/v2/updates/check
   * - Alternativa: GET https://api.github.com/repos/JorgeTato99/universal-camera-viewer/releases/latest
   * 
   * RESPUESTA ESPERADA:
   * {
   *   "version": "0.9.7",
   *   "releaseDate": "2025-01-16T00:00:00Z",
   *   "downloadUrl": "https://github.com/.../release.exe",
   *   "fileSize": 45678901,
   *   "changelog": [
   *     "Mejoras en el rendimiento del streaming",
   *     "Soporte para nuevos modelos de cámaras",
   *     "Corrección de errores"
   *   ],
   *   "isPrerelease": false,
   *   "isMandatory": false
   * }
   * 
   * IMPLEMENTACIÓN SUGERIDA:
   * ```typescript
   * const checkForUpdates = async () => {
   *   setCheckingUpdates(true);
   *   try {
   *     const response = await updateService.checkForUpdates();
   *     setLatestVersion(response.version);
   *     setUpdateAvailable(response.version !== currentVersion);
   *     
   *     // Guardar en store global para mostrar badge en TopBar
   *     useAppStore.setState({ hasUpdate: response.version !== currentVersion });
   *   } catch (error) {
   *     console.error('Error checking updates:', error);
   *     // Mostrar notificación de error al usuario
   *     showNotification({
   *       type: 'error',
   *       message: 'No se pudo verificar actualizaciones'
   *     });
   *   } finally {
   *     setCheckingUpdates(false);
   *   }
   * };
   * ```
   * 
   * NOTA PARA DESARROLLADORES:
   * - Implementar caché de 1 hora para no sobrecargar el servidor
   * - Considerar usar WebSocket para notificaciones push de actualizaciones
   * - El badge de actualización en TopBar debe sincronizarse con este estado
   */
  const checkForUpdates = () => {
    setCheckingUpdates(true);
    // 🔧 MOCK: Simular búsqueda de actualizaciones - REEMPLAZAR CON SERVICIO REAL
    setTimeout(() => {
      setLatestVersion("0.9.7");
      setUpdateAvailable(true);
      setCheckingUpdates(false);
    }, 2000);
  };

  return (
    <>
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      TransitionComponent={Zoom}
      TransitionProps={{
        timeout: 400,
      }}
      PaperProps={{
        sx: {
          borderRadius: borderTokens.radius.lg,
          overflow: "hidden",
          // Sombra más prominente
          boxShadow: theme.shadows[24],
          // Animación de entrada personalizada
          animation: open ? `${fadeInUp} 0.4s ease-out` : "none",
          // Efecto de elevación en hover
          transition: "box-shadow 0.3s ease",
          "&:hover": {
            boxShadow: `0 12px 40px ${alpha(theme.palette.primary.main, 0.15)}`,
          },
        },
      }}
    >
      {/* Header con gradiente animado */}
      <Box
        sx={{
          position: "relative",
          background: `linear-gradient(135deg, ${colorTokens.primary[600]} 0%, ${colorTokens.primary[800]} 100%)`,
          color: "white",
          p: 3,
          pb: 4,
          // Efecto de brillo animado
          "&::before": {
            content: '""',
            position: "absolute",
            top: 0,
            left: "-100%",
            width: "100%",
            height: "100%",
            background: `linear-gradient(90deg, transparent, ${alpha(
              "#ffffff",
              0.1
            )}, transparent)`,
            animation: `${shimmer} 3s infinite`,
          },
          overflow: "hidden",
        }}
      >
        {/* Botón cerrar con animación */}
        <Tooltip title="Cerrar" placement="left" arrow>
          <IconButton
            onClick={onClose}
            sx={{
              position: "absolute",
              right: 8,
              top: 8,
              color: "white",
              transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
              "&:hover": {
                backgroundColor: alpha("#ffffff", 0.2),
                transform: "rotate(90deg) scale(1.1)",
              },
              "&:active": {
                transform: "rotate(180deg) scale(0.9)",
              },
            }}
            aria-label="cerrar"
          >
            <CloseIcon />
          </IconButton>
        </Tooltip>

        {/* Logo y título */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 2,
            mb: 2,
          }}
        >
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: "50%",
              backgroundColor: alpha("#ffffff", 0.2),
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "24px",
              fontWeight: "bold",
              cursor: "pointer",
              transition: "all 0.3s ease",
              animation: `${pulseAnimation} 2s infinite`,
              "&:hover": {
                transform: "scale(1.1)",
                backgroundColor: alpha("#ffffff", 0.3),
              },
            }}
          >
            U
          </Box>
          <Box>
            <Fade in={open} timeout={600}>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                Universal Camera Viewer
              </Typography>
            </Fade>
            <Fade in={open} timeout={800}>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                Sistema Profesional de Videovigilancia IP
              </Typography>
            </Fade>
          </Box>
        </Box>

        {/* Versión con animación */}
        <Fade in={open} timeout={600}>
          <Tooltip title="Versión actual" placement="right" arrow>
            <Chip
              label=" v0.9.6"
              size="small"
              icon={<SparkleIcon sx={{ fontSize: 16 }} />}
              sx={{
                backgroundColor: alpha("#ffffff", 0.2),
                color: "white",
                fontWeight: 500,
                transition: "all 0.3s ease",
                "&:hover": {
                  backgroundColor: alpha("#ffffff", 0.4),
                  transform: "scale(1.08)",
                  boxShadow: `0 0 12px ${alpha("#ffffff", 0.3)}`,
                },
              }}
            />
          </Tooltip>
        </Fade>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs 
          value={currentTab} 
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{
            "& .MuiTab-root": {
              textTransform: "none",
              fontWeight: 500,
              transition: "all 0.3s ease",
              "&:hover": {
                backgroundColor: alpha(colorTokens.primary[500], 0.05),
              },
            },
          }}
        >
          <Tab 
            label="Información" 
            icon={<InfoIcon fontSize="small" />} 
            iconPosition="start"
            sx={{ gap: 1 }}
          />
          <Tab 
            label="Actualizaciones" 
            icon={
              updateAvailable ? (
                <Badge color="error" variant="dot">
                  <UpdateIcon fontSize="small" />
                </Badge>
              ) : (
                <UpdateIcon fontSize="small" />
              )
            } 
            iconPosition="start"
            sx={{ gap: 1 }}
          />
          <Tab 
            label="Licencia" 
            icon={<LicenseIcon fontSize="small" />} 
            iconPosition="start"
            sx={{ gap: 1 }}
          />
        </Tabs>
      </Box>

      <DialogContent sx={{ p: 3 }}>
        {/* Tab 1: Información */}
        <TabPanel value={currentTab} index={0}>
          {/* Descripción con skeleton loader */}
          {!contentLoaded ? (
            <>
              <Skeleton variant="text" sx={{ fontSize: "1rem", mb: 2 }} />
              <Skeleton variant="text" sx={{ fontSize: "1rem", width: "80%" }} />
            </>
          ) : (
            <Fade in={contentLoaded} timeout={500}>
              <Typography variant="body1" paragraph>
                Una solución completa para la gestión y monitoreo de cámaras IP
                con soporte para múltiples protocolos y fabricantes.
              </Typography>
            </Fade>
          )}

        {/* Características principales */}
        <Box sx={{ mb: 3 }}>
          {!contentLoaded ? (
            <Skeleton
              variant="rectangular"
              height={20}
              width={180}
              sx={{ mb: 2 }}
            />
          ) : (
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
              Características Principales
            </Typography>
          )}

          <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
            {[
              {
                icon: CameraIcon,
                color: colorTokens.primary[500],
                text: "Streaming en tiempo real con WebSocket",
              },
              {
                icon: SecurityIcon,
                color: colorTokens.status.connected,
                text: "Soporte ONVIF, RTSP y HTTP/CGI",
              },
              {
                icon: PerformanceIcon,
                color: colorTokens.status.connecting,
                text: "Alto rendimiento: 15+ FPS, <300MB RAM",
              },
            ].map((feature, index) => (
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1.5,
                  transition: "all 0.3s ease",
                  borderRadius: 1,
                  p: 0.5,
                  "&:hover": {
                    backgroundColor: alpha(theme.palette.primary.main, 0.05),
                  },
                }}
              >
                <feature.icon
                  sx={{
                    color: feature.color,
                    fontSize: 20,
                    transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                  }}
                />
                <Typography variant="body2">{feature.text}</Typography>
              </Box>
            ))}
          </Box>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Información técnica */}
        <Box sx={{ mb: 3 }}>
          {!contentLoaded ? (
            <Skeleton
              variant="rectangular"
              height={20}
              width={150}
              sx={{ mb: 2 }}
            />
          ) : (
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
              Stack Tecnológico
            </Typography>
          )}

          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
            {!contentLoaded
              ? // Skeleton para chips
                Array.from({ length: 6 }).map((_, index) => (
                  <Skeleton
                    key={index}
                    variant="rectangular"
                    width={80 + Math.random() * 40}
                    height={24}
                    sx={{ borderRadius: 16 }}
                  />
                ))
              : [
                  "React 19",
                  "TypeScript",
                  "Material-UI v5",
                  "FastAPI",
                  "Python 3.8+",
                  "SQLite 3FN",
                ].map((tech, index) => (
                  <Zoom
                    key={tech}
                    in={open}
                    timeout={600}
                    style={{ transitionDelay: `${index * 100}ms` }}
                  >
                    <Chip
                      label={tech}
                      size="small"
                      variant="outlined"
                      sx={{
                        transition: "all 0.3s ease",
                        cursor: "pointer",
                        "&:hover": {
                          transform: "translateY(-3px)",
                          boxShadow: theme.shadows[4],
                          backgroundColor: alpha(
                            theme.palette.primary.main,
                            0.05
                          ),
                          borderColor: theme.palette.primary.main,
                        },
                      }}
                    />
                  </Zoom>
                ))}
          </Box>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Enlaces */}
        <Box>
          {!contentLoaded ? (
            <Skeleton
              variant="rectangular"
              height={20}
              width={160}
              sx={{ mb: 2 }}
            />
          ) : (
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
              Enlaces y Recursos
            </Typography>
          )}

          <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
            {!contentLoaded
              ? // Skeleton para enlaces
                Array.from({ length: 2 }).map((_, index) => (
                  <Skeleton
                    key={index}
                    variant="rectangular"
                    height={40}
                    sx={{ borderRadius: 1 }}
                  />
                ))
              : [
                  {
                    icon: GitHubIcon,
                    text: "Repositorio en GitHub",
                    href: "https://github.com/JorgeTato99/universal-camera-viewer",
                  },
                  {
                    icon: WebIcon,
                    text: "Documentación API",
                    href: "http://localhost:8000/docs",
                  },
                ].map((link, index) => (
                  <Tooltip
                    key={index}
                    title={`Abrir ${link.text}`}
                    placement="right"
                  >
                    <Link
                      href={link.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 1,
                        color: theme.palette.text.primary,
                        textDecoration: "none",
                        p: 1,
                        borderRadius: 1,
                        transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                        position: "relative",
                        overflow: "hidden",
                        "&::after": {
                          content: '""',
                          position: "absolute",
                          bottom: 0,
                          left: 0,
                          width: "100%",
                          height: "2px",
                          backgroundColor: theme.palette.primary.main,
                          transform: "scaleX(0)",
                          transformOrigin: "left",
                          transition: "transform 0.3s ease",
                        },
                        "&:hover": {
                          backgroundColor: alpha(
                            theme.palette.primary.main,
                            0.05
                          ),
                          transform: "translateX(4px)",
                          "& svg": {
                            transform: "rotate(-10deg) scale(1.1)",
                            color: theme.palette.primary.main,
                          },
                          "&::after": {
                            transform: "scaleX(1)",
                          },
                        },
                      }}
                    >
                      <link.icon
                        fontSize="small"
                        sx={{
                          transition: "transform 0.3s ease",
                        }}
                      />
                      <Typography variant="body2">{link.text}</Typography>
                    </Link>
                  </Tooltip>
                ))}
          </Box>
        </Box>

        {/* Créditos con animación */}
        <Fade in={contentLoaded} timeout={1000}>
          <Box
            sx={{
              mt: 3,
              pt: 2,
              borderTop: 1,
              borderColor: "divider",
              textAlign: "center",
              opacity: 0.8,
              transition: "all 0.3s ease",
              "&:hover": {
                opacity: 1,
                "& .floating-heart": {
                  animation: `${floatAnimation} 1s ease-in-out infinite`,
                },
              },
            }}
          >
            <Typography variant="caption" color="text.secondary">
              © 2025 Universal Camera Viewer
            </Typography>
            <Typography
              variant="caption"
              display="block"
              color="text.secondary"
              sx={{ mt: 0.5 }}
            >
              Software propiedad de <strong>Kipustec</strong>
            </Typography>
            <Typography
              variant="caption"
              display="block"
              color="text.secondary"
              sx={{ mt: 0.5 }}
            >
              Desarrollado con <span className="floating-heart">❤️</span> por
              Jorge Tato
            </Typography>
          </Box>
        </Fade>
        </TabPanel>

        {/* Tab 2: Actualizaciones */}
        <TabPanel value={currentTab} index={1}>
          <Box>
            {/* Estado actual */}
            <Paper
              variant="outlined"
              sx={{
                p: 3,
                mb: 3,
                borderRadius: borderTokens.radius.md,
                backgroundColor: updateAvailable
                  ? alpha(colorTokens.status.connecting, 0.05)
                  : alpha(colorTokens.status.connected, 0.05),
                border: `1px solid ${
                  updateAvailable
                    ? alpha(colorTokens.status.connecting, 0.3)
                    : alpha(colorTokens.status.connected, 0.3)
                }`,
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: "50%",
                    backgroundColor: updateAvailable
                      ? alpha(colorTokens.status.connecting, 0.1)
                      : alpha(colorTokens.status.connected, 0.1),
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: updateAvailable
                      ? colorTokens.status.connecting
                      : colorTokens.status.connected,
                  }}
                >
                  {updateAvailable ? <UpdateIcon /> : <CheckIcon />}
                </Box>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    {updateAvailable
                      ? `Nueva versión ${latestVersion} disponible`
                      : "Sistema actualizado"}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Versión actual: {currentVersion}
                  </Typography>
                </Box>
                {updateAvailable && (
                  <Button
                    variant="contained"
                    startIcon={<DownloadIcon />}
                    onClick={() => {
                      /**
                       * 🚀 INTEGRACIÓN PENDIENTE - Descargar Actualización
                       * 
                       * TODO: Implementar descarga de actualización
                       * 
                       * OPCIÓN 1 - Abrir en navegador:
                       * window.open(downloadUrl, '_blank');
                       * 
                       * OPCIÓN 2 - Descarga con progreso usando Tauri:
                       * ```typescript
                       * import { download } from '@tauri-apps/api/http';
                       * import { save } from '@tauri-apps/api/dialog';
                       * 
                       * const filePath = await save({
                       *   defaultPath: `UniversalCameraViewer_${latestVersion}.exe`
                       * });
                       * 
                       * if (filePath) {
                       *   await download(downloadUrl, filePath, {
                       *     onDownloadProgress: (progress) => {
                       *       setDownloadProgress(progress.percentage);
                       *     }
                       *   });
                       * }
                       * ```
                       */
                      console.log("🔧 MOCK: Descargar actualización - IMPLEMENTAR");
                    }}
                    sx={{
                      textTransform: "none",
                      borderRadius: borderTokens.radius.md,
                    }}
                  >
                    Descargar
                  </Button>
                )}
              </Box>

              {updateAvailable && (
                <Box>
                  <Typography
                    variant="subtitle2"
                    sx={{ fontWeight: 600, mb: 1 }}
                  >
                    Novedades en la versión {latestVersion}:
                  </Typography>
                  <Box component="ul" sx={{ m: 0, pl: 3 }}>
                    <Typography component="li" variant="body2" sx={{ mb: 0.5 }}>
                      Mejoras en el rendimiento del streaming
                    </Typography>
                    <Typography component="li" variant="body2" sx={{ mb: 0.5 }}>
                      Soporte para nuevos modelos de cámaras Hikvision
                    </Typography>
                    <Typography component="li" variant="body2" sx={{ mb: 0.5 }}>
                      Corrección de errores en el escaneo de red
                    </Typography>
                    <Typography component="li" variant="body2">
                      Actualización de dependencias de seguridad
                    </Typography>
                  </Box>
                </Box>
              )}
            </Paper>

            {/* Botón buscar actualizaciones */}
            <Box sx={{ textAlign: "center" }}>
              <Button
                variant="outlined"
                startIcon={
                  checkingUpdates ? (
                    <CircularProgress size={16} />
                  ) : (
                    <UpdateIcon />
                  )
                }
                onClick={checkForUpdates}
                disabled={checkingUpdates}
                sx={{
                  textTransform: "none",
                  borderRadius: borderTokens.radius.md,
                  minWidth: 200,
                }}
              >
                {checkingUpdates
                  ? "Buscando actualizaciones..."
                  : "Buscar actualizaciones"}
              </Button>
            </Box>

            {/* Configuración de actualizaciones */}
            <Box sx={{ mt: 4 }}>
              <Typography
                variant="subtitle2"
                sx={{ fontWeight: 600, mb: 2 }}
              >
                Configuración de actualizaciones
              </Typography>
              <Alert severity="info" variant="outlined">
                Las actualizaciones automáticas se pueden configurar en{" "}
                <Link
                  component="button"
                  onClick={() => {
                    onClose();
                    /**
                     * 🚀 INTEGRACIÓN PENDIENTE - Navegación a Configuración
                     * 
                     * TODO: Implementar navegación programática a settings
                     * 
                     * IMPLEMENTACIÓN:
                     * ```typescript
                     * import { useNavigate } from 'react-router-dom';
                     * 
                     * const navigate = useNavigate();
                     * onClose();
                     * navigate('/settings/general/updates');
                     * ```
                     * 
                     * ALTERNATIVA con store global:
                     * ```typescript
                     * useAppStore.setState({ 
                     *   activeSettingsTab: 'general',
                     *   activeSettingsSection: 'updates'
                     * });
                     * navigate('/settings');
                     * ```
                     */
                    console.log("🔧 MOCK: Navegar a configuración - IMPLEMENTAR");
                  }}
                  sx={{ fontWeight: 500 }}
                >
                  Configuración → General → Actualizaciones
                </Link>
              </Alert>
            </Box>
          </Box>
        </TabPanel>

        {/* Tab 3: Licencia */}
        <TabPanel value={currentTab} index={2}>
          <Box>
            <Paper
              variant="outlined"
              sx={{
                p: 3,
                mb: 3,
                borderRadius: borderTokens.radius.md,
                backgroundColor: theme.palette.mode === "dark"
                  ? "rgba(255, 255, 255, 0.02)"
                  : "rgba(0, 0, 0, 0.01)",
              }}
            >
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Licencia de Software
              </Typography>
              <Typography variant="body2" paragraph>
                Universal Camera Viewer es un software propietario desarrollado
                por Kipustec. Todos los derechos reservados.
              </Typography>
              <Typography variant="body2" paragraph>
                Este software está protegido por las leyes de derechos de autor
                y tratados internacionales. La reproducción o distribución no
                autorizada de este programa, o cualquier parte del mismo, puede
                resultar en severas sanciones civiles y penales.
              </Typography>
              <Box
                sx={{
                  mt: 2,
                  p: 2,
                  borderRadius: 1,
                  backgroundColor: theme.palette.mode === "dark"
                    ? "rgba(255, 255, 255, 0.05)"
                    : "rgba(0, 0, 0, 0.02)",
                  fontFamily: "monospace",
                  fontSize: "0.875rem",
                  maxHeight: 200,
                  overflow: "auto",
                }}
              >
                <Typography variant="body2" component="pre" sx={{ m: 0 }}>
{`LICENCIA DE SOFTWARE PROPIETARIO
Version 1.0 - Enero 2025

TÉRMINOS Y CONDICIONES

1. CONCESIÓN DE LICENCIA
Kipustec le otorga una licencia no exclusiva e 
intransferible para usar el software Universal 
Camera Viewer.

2. RESTRICCIONES
Usted NO puede:
- Copiar o distribuir el software
- Realizar ingeniería inversa
- Modificar o crear trabajos derivados
- Sublicenciar o transferir la licencia

3. PROPIEDAD
Este software es propiedad de Kipustec y está 
protegido por leyes de propiedad intelectual.

4. GARANTÍA LIMITADA
El software se proporciona "tal cual" sin 
garantías de ningún tipo.

5. LIMITACIÓN DE RESPONSABILIDAD
Kipustec no será responsable por daños 
indirectos o consecuentes.`}
                </Typography>
              </Box>
            </Paper>

            {/* Botones de acción */}
            <Box sx={{ display: "flex", gap: 2, justifyContent: "center" }}>
              <Button
                variant="outlined"
                startIcon={<OpenIcon />}
                onClick={() => {
                  setLicenseDialogOpen(true);
                }}
                sx={{
                  textTransform: "none",
                  borderRadius: borderTokens.radius.md,
                }}
              >
                Ver licencia completa
              </Button>
              <Button
                variant="outlined"
                onClick={() => {
                  /**
                   * 🚀 INTEGRACIÓN PENDIENTE - Exportar Licencia a PDF
                   * 
                   * TODO: Implementar exportación de licencia
                   * 
                   * OPCIÓN 1 - Usando jsPDF (recomendado):
                   * ```typescript
                   * import { jsPDF } from 'jspdf';
                   * 
                   * const doc = new jsPDF();
                   * doc.setFontSize(16);
                   * doc.text('LICENCIA DE SOFTWARE', 20, 20);
                   * doc.setFontSize(12);
                   * doc.text(FULL_LICENSE_TEXT, 20, 40, { maxWidth: 170 });
                   * doc.save('Universal_Camera_Viewer_Licencia.pdf');
                   * ```
                   * 
                   * OPCIÓN 2 - Backend endpoint:
                   * ```typescript
                   * const response = await fetch('/api/v2/license/export/pdf');
                   * const blob = await response.blob();
                   * const url = URL.createObjectURL(blob);
                   * const a = document.createElement('a');
                   * a.href = url;
                   * a.download = 'Universal_Camera_Viewer_Licencia.pdf';
                   * a.click();
                   * ```
                   * 
                   * NOTA: Si se usa jsPDF, instalar con:
                   * yarn add jspdf @types/jspdf
                   */
                  console.log("🔧 MOCK: Exportar licencia PDF - IMPLEMENTAR");
                }}
                sx={{
                  textTransform: "none",
                  borderRadius: borderTokens.radius.md,
                }}
              >
                Exportar PDF
              </Button>
            </Box>

            {/* Información adicional */}
            <Box sx={{ mt: 4 }}>
              <Alert severity="info" variant="outlined">
                Para más información sobre licenciamiento, contacte a{" "}
                <Link href="mailto:licencias@kipustec.com">
                  licencias@kipustec.com
                </Link>
              </Alert>
            </Box>
          </Box>
        </TabPanel>
      </DialogContent>
    </Dialog>
    
    {/* License Dialog */}
    <LicenseDialog 
      open={licenseDialogOpen} 
      onClose={() => setLicenseDialogOpen(false)} 
    />
    </>
  );
};
