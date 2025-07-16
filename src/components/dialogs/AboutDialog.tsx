/**
 * 🎯 About Dialog Component - Universal Camera Viewer
 * Dialog de información sobre la aplicación
 */

import React from "react";
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
} from "@mui/icons-material";
import {
  colorTokens,
  borderTokens,
  spacingTokens,
} from "../../design-system/tokens";

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

export const AboutDialog: React.FC<AboutDialogProps> = ({ open, onClose }) => {
  const theme = useTheme();
  const [contentLoaded, setContentLoaded] = React.useState(false);
  const [rippleActive, setRippleActive] = React.useState(false);

  React.useEffect(() => {
    if (open) {
      // Simular carga de contenido
      const timer = setTimeout(() => setContentLoaded(true), 300);
      return () => clearTimeout(timer);
    } else {
      setContentLoaded(false);
    }
  }, [open]);

  return (
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

      <DialogContent sx={{ p: 3 }}>
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
      </DialogContent>
    </Dialog>
  );
};
