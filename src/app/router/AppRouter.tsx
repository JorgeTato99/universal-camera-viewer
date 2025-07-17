import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";

// Feature pages (will be created later)
const LiveViewPage = React.lazy(
  () => import("../../features/cameras/pages/LiveViewPage")
);
const RegisterPage = React.lazy(
  () => import("../../features/cameras/pages/management/CameraManagementPage")
);
const ScannerPage = React.lazy(
  () => import("../../features/scanner/ScannerPage")
);
const AnalyticsPage = React.lazy(
  () => import("../../features/analytics/AnalyticsPage")
);
const SettingsPage = React.lazy(
  () => import("../../features/settings/SettingsPage")
);

// Error Boundary component
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(_: Error) {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Router Error Boundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            padding: "2rem",
            textAlign: "center",
            minHeight: "50vh",
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
          }}
        >
          <h2>Algo salió mal</h2>
          <p>Ha ocurrido un error inesperado. Por favor, recarga la página.</p>
          <button
            onClick={() => window.location.reload()}
            style={{
              margin: "1rem auto",
              padding: "0.5rem 1rem",
              background: "#1976d2",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            Recargar Página
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Loading fallback component
const LoadingFallback: React.FC = () => (
  <div
    style={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      minHeight: "50vh",
      fontSize: "1.2rem",
      color: "#666",
    }}
  >
    Cargando...
  </div>
);

export const AppRouter: React.FC = () => {
  return (
    <ErrorBoundary>
      <React.Suspense fallback={<LoadingFallback />}>
        <Routes>
          {/* Default redirect to cameras */}
          <Route path="/" element={<Navigate to="/cameras/live" replace />} />

          {/* Main feature routes */}
          <Route path="/cameras" element={<Navigate to="/cameras/live" replace />} />
          <Route path="/cameras/live" element={<LiveViewPage />} />
          <Route path="/cameras/register" element={<RegisterPage />} />
          <Route path="/scanner" element={<ScannerPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/settings" element={<SettingsPage />} />

          {/* Catch-all route for 404 */}
          <Route
            path="*"
            element={
              <div
                style={{
                  padding: "2rem",
                  textAlign: "center",
                  minHeight: "50vh",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "center",
                }}
              >
                <h2>Página no encontrada</h2>
                <p>La página que buscas no existe.</p>
                <a
                  href="/cameras"
                  style={{ color: "#1976d2", textDecoration: "none" }}
                >
                  Volver a Cámaras
                </a>
              </div>
            }
          />
        </Routes>
      </React.Suspense>
    </ErrorBoundary>
  );
};

export default AppRouter;
