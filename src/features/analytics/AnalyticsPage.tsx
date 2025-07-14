import React from "react";
import { Box, Typography, Paper } from "@mui/material";

const AnalyticsPage: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Analytics y Métricas
      </Typography>

      <Paper sx={{ p: 3, mt: 2 }}>
        <Typography variant="h6" gutterBottom>
          📊 Dashboard de Métricas
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Esta página mostrará métricas detalladas del sistema y cámaras.
        </Typography>
        <ul>
          <li>Métricas de streaming</li>
          <li>Performance del sistema</li>
          <li>Estadísticas de conexión</li>
          <li>Gráficos en tiempo real</li>
        </ul>
      </Paper>
    </Box>
  );
};

export default AnalyticsPage;
