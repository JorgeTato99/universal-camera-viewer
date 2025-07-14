import React, { useEffect } from "react";
import { Box, AppBar, Toolbar, Typography, Button } from "@mui/material";
import { useNavigate, useLocation } from "react-router-dom";
import AppProviders from "./app/providers/AppProviders";
import AppRouter from "./app/router/AppRouter";
import { useAppStore } from "./stores";

// Navigation component
const NavigationBar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: "/cameras", label: "Cámaras", icon: "🎥" },
    { path: "/scanner", label: "Escáner", icon: "🔍" },
    { path: "/analytics", label: "Analytics", icon: "📊" },
    { path: "/settings", label: "Configuración", icon: "⚙️" },
  ];

  return (
    <AppBar position="static" elevation={1}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Universal Camera Viewer
        </Typography>

        <Box sx={{ display: "flex", gap: 1 }}>
          {navItems.map((item) => (
            <Button
              key={item.path}
              color="inherit"
              onClick={() => navigate(item.path)}
              variant={location.pathname === item.path ? "outlined" : "text"}
              sx={{
                borderColor: "white",
                color: "white",
                "&:hover": {
                  backgroundColor: "rgba(255, 255, 255, 0.1)",
                },
              }}
            >
              {item.icon} {item.label}
            </Button>
          ))}
        </Box>
      </Toolbar>
    </AppBar>
  );
};

// Main App Layout
const AppLayout: React.FC = () => {
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
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <NavigationBar />

      <Box
        component="main"
        sx={{ flexGrow: 1, backgroundColor: "background.default" }}
      >
        <AppRouter />
      </Box>

      {/* Status bar could go here */}
      <Box
        component="footer"
        sx={{
          p: 1,
          backgroundColor: "background.paper",
          borderTop: 1,
          borderColor: "divider",
          textAlign: "center",
        }}
      >
        <Typography variant="caption" color="text.secondary">
          Universal Camera Viewer v2.0.0 - Arquitectura React + Tauri
        </Typography>
      </Box>
    </Box>
  );
};

// Root App Component
const App: React.FC = () => {
  return (
    <AppProviders>
      <AppLayout />
    </AppProviders>
  );
};

export default App;
