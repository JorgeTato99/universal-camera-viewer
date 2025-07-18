import React, { useEffect, memo } from "react";
import { Box, Typography, Button } from "@mui/material";
import AppProviders from "./app/providers/AppProviders";
import AppRouter from "./app/router/AppRouter";
import { useAppStore } from "./stores";
import { MainLayout } from "./components/layout";

// Main App Layout optimizado con memo
const AppLayout = memo(() => {
  const { initialize, isInitializing, globalError } = useAppStore();

  useEffect(() => {
    // Initialize the app
    initialize();
  }, [initialize]);

  if (isInitializing) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "100vh",
          flexDirection: "column",
          gap: 2,
        }}
      >
        <Typography variant="h5">Universal Camera Viewer</Typography>
        <Typography variant="body1" color="text.secondary">
          Inicializando aplicación...
        </Typography>
      </Box>
    );
  }

  if (globalError) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "100vh",
          flexDirection: "column",
          gap: 2,
          p: 3,
        }}
      >
        <Typography variant="h5" color="error">
          Error de Inicialización
        </Typography>
        <Typography variant="body1" color="text.secondary" textAlign="center">
          {globalError}
        </Typography>
        <Button variant="contained" onClick={() => window.location.reload()}>
          Recargar Aplicación
        </Button>
      </Box>
    );
  }

  return (
    <MainLayout>
      <AppRouter />
    </MainLayout>
  );
});

// Añadir displayName para debugging
AppLayout.displayName = 'AppLayout';

// Root App Component
const App: React.FC = () => {
  return (
    <AppProviders>
      <AppLayout />
    </AppProviders>
  );
};

export default App;
