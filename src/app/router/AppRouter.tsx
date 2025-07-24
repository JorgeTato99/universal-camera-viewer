import React, { memo, Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { Box, CircularProgress, Typography } from "@mui/material";

// Feature pages con lazy loading optimizado
const LiveViewPage = React.lazy(
  () => import("../../features/cameras/pages/LiveViewPage")
);
const RegisterPage = React.lazy(
  () => import("../../features/cameras/pages/management/CameraManagementPage")
);
// Scanner pages
const ScannerPage = React.lazy(
  () => import("../../features/scanner/ScannerPage")
);
const NetworkScanPage = React.lazy(
  () => import("../../features/scanner/pages/network/NetworkScanPage")
);
const PortScanPage = React.lazy(
  () => import("../../features/scanner/pages/ports/PortScanPage")
);
const AccessTestPage = React.lazy(
  () => import("../../features/scanner/pages/access/AccessTestPage")
);
// Removed old AnalyticsPage - now using StatisticsPage
const StatisticsPage = React.lazy(
  () => import("../../features/statistics/pages/StatisticsPage")
);
const SettingsPage = React.lazy(
  () => import("../../features/settings/SettingsPage")
);

// Publishing pages
const PublishingDashboard = React.lazy(
  () => import("../../features/publishing/pages/PublishingDashboard")
);
const ActivePublications = React.lazy(
  () => import("../../features/publishing/pages/ActivePublications")
);
const PublishingMetrics = React.lazy(
  () => import("../../features/publishing/pages/PublishingMetrics")
);
const PublishingHistory = React.lazy(
  () => import("../../features/publishing/pages/PublishingHistory")
);
const PathConfiguration = React.lazy(
  () => import("../../features/publishing/pages/PathConfiguration")
);
const MediaMTXServersPage = React.lazy(
  () => import("../../features/publishing/pages/MediaMTXServersPage")
);

// Precargar páginas críticas para mejorar la experiencia
const preloadCriticalPages = () => {
  // Precargar LiveViewPage ya que es la página principal
  import("../../features/cameras/pages/LiveViewPage");
};

// Error Boundary component mejorado
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Router Error Boundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "50vh",
            p: 3,
            textAlign: "center",
          }}
        >
          <Typography variant="h5" gutterBottom color="error">
            Algo salió mal
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            Ha ocurrido un error inesperado. Por favor, recarga la página.
          </Typography>
          {process.env.NODE_ENV === "development" && this.state.error && (
            <Box
              sx={{
                mt: 2,
                p: 2,
                bgcolor: "grey.100",
                borderRadius: 1,
                maxWidth: 600,
                width: "100%",
              }}
            >
              <Typography
                variant="caption"
                component="pre"
                sx={{
                  fontFamily: "monospace",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                }}
              >
                {this.state.error.toString()}
              </Typography>
            </Box>
          )}
          <Box sx={{ mt: 3 }}>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: "8px 24px",
                background: "#1976d2",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "14px",
                fontWeight: 500,
              }}
            >
              Recargar Página
            </button>
          </Box>
        </Box>
      );
    }

    return this.props.children;
  }
}

// Loading fallback component mejorado con Material-UI
const LoadingFallback = memo(() => (
  <Box
    sx={{
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      alignItems: "center",
      minHeight: "50vh",
      gap: 2,
    }}
  >
    <CircularProgress size={40} />
    <Typography variant="body1" color="text.secondary">
      Cargando...
    </Typography>
  </Box>
));

LoadingFallback.displayName = "LoadingFallback";

// Componente 404 memoizado
const NotFoundPage = memo(() => (
  <Box
    sx={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      minHeight: "50vh",
      p: 3,
      textAlign: "center",
    }}
  >
    <Typography variant="h1" sx={{ fontSize: "6rem", fontWeight: 300 }}>
      404
    </Typography>
    <Typography variant="h5" gutterBottom>
      Página no encontrada
    </Typography>
    <Typography variant="body1" color="text.secondary" paragraph>
      La página que buscas no existe.
    </Typography>
    <a
      href="/cameras"
      style={{
        color: "#1976d2",
        textDecoration: "none",
        marginTop: "16px",
        fontSize: "16px",
      }}
    >
      Volver a Cámaras
    </a>
  </Box>
));

NotFoundPage.displayName = "NotFoundPage";

export const AppRouter = memo(() => {
  // Precargar páginas críticas cuando el componente se monta
  React.useEffect(() => {
    // Dar tiempo para que la página inicial cargue antes de precargar otras
    const timer = setTimeout(() => {
      preloadCriticalPages();
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          {/* Default redirect to cameras */}
          <Route path="/" element={<Navigate to="/cameras/live" replace />} />

          {/* Main feature routes */}
          <Route path="/cameras" element={<Navigate to="/cameras/live" replace />} />
          <Route path="/cameras/live" element={<LiveViewPage />} />
          <Route path="/cameras/register" element={<RegisterPage />} />
          {/* Scanner routes with sub-pages */}
          <Route path="/scanner" element={<ScannerPage />} />
          <Route path="/scanner/network" element={<NetworkScanPage />} />
          <Route path="/scanner/ports" element={<PortScanPage />} />
          <Route path="/scanner/access" element={<AccessTestPage />} />
          {/* Statistics routes with sub-pages */}
          <Route path="/statistics" element={<StatisticsPage />} />
          <Route path="/statistics/:subpage" element={<StatisticsPage />} />
          
          {/* Publishing routes */}
          <Route path="/publishing" element={<Navigate to="/publishing/dashboard" replace />} />
          <Route path="/publishing/dashboard" element={<PublishingDashboard />} />
          <Route path="/publishing/servers" element={<MediaMTXServersPage />} />
          <Route path="/publishing/active" element={<ActivePublications />} />
          <Route path="/publishing/metrics" element={<PublishingMetrics />} />
          <Route path="/publishing/history" element={<PublishingHistory />} />
          <Route path="/publishing/paths" element={<PathConfiguration />} />
          
          <Route path="/settings" element={<SettingsPage />} />

          {/* Catch-all route for 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </ErrorBoundary>
  );
});

// Añadir displayName para debugging
AppRouter.displayName = "AppRouter";

export default AppRouter;