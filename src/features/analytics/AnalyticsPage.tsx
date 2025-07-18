/**
 * 📊 Analytics Page - Universal Camera Viewer
 * Página de análisis y métricas del sistema
 * Optimizada con memo y lazy loading de componentes
 */

import { memo, Suspense } from "react";
import { 
  Box, 
  Typography, 
  Paper, 
  Skeleton,
  CircularProgress,
  Container,
  Fade,
  Grow 
} from "@mui/material";

// Lazy loading de futuros componentes de gráficos
// const MetricsChart = lazy(() => import("./components/MetricsChart"));
// const PerformanceStats = lazy(() => import("./components/PerformanceStats"));

/**
 * Componente de carga para Suspense
 */
const LoadingFallback = memo(() => (
  <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
    <CircularProgress />
  </Box>
));

LoadingFallback.displayName = 'LoadingFallback';

/**
 * Página de Analytics optimizada con memo
 * Evita re-renders innecesarios al no tener props
 */
const AnalyticsPage = memo(() => {
  return (
    <Fade in timeout={600}>
      <Container maxWidth="xl">
        <Box sx={{ py: 3 }}>
          {/* Header con animación */}
          <Fade in timeout={500} style={{ transitionDelay: '100ms' }}>
            <Typography variant="h4" component="h1" gutterBottom>
              Analytics y Métricas
            </Typography>
          </Fade>

          <Grow in timeout={800} style={{ transitionDelay: '200ms', transformOrigin: '0 0 0' }}>
            <Paper 
              sx={{ 
                p: 3, 
                mt: 2,
                // Optimización: usar will-change para animaciones futuras
                willChange: 'transform',
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: 3,
                }
              }}
            >
              <Fade in timeout={600} style={{ transitionDelay: '300ms' }}>
                <Box>
                  <Typography variant="h6" gutterBottom>
                    📊 Dashboard de Métricas
                  </Typography>
                  <Typography variant="body1" color="text.secondary" paragraph>
                    Esta página mostrará métricas detalladas del sistema y cámaras.
                  </Typography>
                </Box>
              </Fade>
              
              {/* Suspense para futuros componentes */}
              <Suspense fallback={<LoadingFallback />}>
                <Fade in timeout={700} style={{ transitionDelay: '400ms' }}>
                  <Box component="section" sx={{ mt: 2 }}>
                    <Typography variant="subtitle1" gutterBottom fontWeight={600}>
                      Funcionalidades planeadas:
                    </Typography>
                    <Box component="ul" sx={{ pl: 2 }}>
                      {['Métricas de streaming en tiempo real',
                        'Performance del sistema (CPU, memoria, red)',
                        'Estadísticas de conexión por cámara',
                        'Gráficos interactivos con históricos'].map((item, index) => (
                        <Fade 
                          key={index} 
                          in 
                          timeout={500} 
                          style={{ transitionDelay: `${500 + index * 100}ms` }}
                        >
                          <Typography component="li" variant="body2" sx={{ mb: 0.5 }}>
                            {item}
                          </Typography>
                        </Fade>
                      ))}
                    </Box>
                  </Box>
                </Fade>
              </Suspense>

              {/* Skeleton para demostrar carga futura de gráficos con animación */}
              <Fade in timeout={800} style={{ transitionDelay: '900ms' }}>
                <Box sx={{ mt: 4 }}>
                  <Skeleton 
                    variant="rectangular" 
                    height={300} 
                    sx={{ 
                      borderRadius: 1,
                      animation: 'pulse 1.5s ease-in-out infinite',
                      '@keyframes pulse': {
                        '0%': { opacity: 0.6 },
                        '50%': { opacity: 1 },
                        '100%': { opacity: 0.6 },
                      }
                    }} 
                  />
                </Box>
              </Fade>
            </Paper>
          </Grow>
        </Box>
      </Container>
    </Fade>
  );
});

// Añadir displayName para debugging
AnalyticsPage.displayName = 'AnalyticsPage';

export default AnalyticsPage;
