import React from "react";
import { Box, Typography, Paper } from "@mui/material";

const CamerasPage: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Gestión de Cámaras
      </Typography>

      <Paper sx={{ p: 3, mt: 2 }}>
        <Typography variant="h6" gutterBottom>
          🎥 Página de Cámaras
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Esta página mostrará la gestión completa de cámaras IP.
          <br />
          Funcionalidades a implementar:
        </Typography>
        <ul>
          <li>Grid de cámaras conectadas</li>
          <li>Vista en tiempo real</li>
          <li>Controles de conexión</li>
          <li>Configuración de cámaras</li>
          <li>Captura de snapshots</li>
        </ul>
      </Paper>
    </Box>
  );
};

export default CamerasPage;
