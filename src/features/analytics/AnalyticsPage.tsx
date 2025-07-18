/**
 * 📊 Analytics Page - Universal Camera Viewer
 * Página de análisis y métricas del sistema
 * Optimizada con memo y lazy loading de componentes
 */

import React, { memo, Suspense, lazy } from "react";
import { 
  Box, 
  Typography, 
  Paper, 
  Skeleton,
  CircularProgress,
  Container 
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
    <Container maxWidth="xl">
      <Box sx={{ py: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Analytics y Métricas
        </Typography>

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
          <Typography variant="h6" gutterBottom>
            📊 Dashboard de Métricas
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            Esta página mostrará métricas detalladas del sistema y cámaras.
          </Typography>
          
          {/* Suspense para futuros componentes */}
          <Suspense fallback={<LoadingFallback />}>
            <Box component="section" sx={{ mt: 2 }}>
              <Typography variant="subtitle1" gutterBottom fontWeight={600}>
                Funcionalidades planeadas:
              </Typography>
              <Box component="ul" sx={{ pl: 2 }}>
                <Typography component="li" variant="body2" sx={{ mb: 0.5 }}>
                  Métricas de streaming en tiempo real
                </Typography>
                <Typography component="li" variant="body2" sx={{ mb: 0.5 }}>
                  Performance del sistema (CPU, memoria, red)
                </Typography>
                <Typography component="li" variant="body2" sx={{ mb: 0.5 }}>
                  Estadísticas de conexión por cámara
                </Typography>
                <Typography component="li" variant="body2" sx={{ mb: 0.5 }}>
                  Gráficos interactivos con históricos
                </Typography>
              </Box>
            </Box>
          </Suspense>

          {/* Skeleton para demostrar carga futura de gráficos */}
          <Box sx={{ mt: 4 }}>
            <Skeleton variant="rectangular" height={300} sx={{ borderRadius: 1 }} />
          </Box>
        </Paper>
      </Box>
    </Container>
  );
});

// Añadir displayName para debugging
AnalyticsPage.displayName = 'AnalyticsPage';

export default AnalyticsPage;
