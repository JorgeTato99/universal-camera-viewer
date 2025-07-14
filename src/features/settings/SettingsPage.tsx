import React from "react";
import { Box, Typography, Paper } from "@mui/material";

const SettingsPage: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Configuración
      </Typography>

      <Paper sx={{ p: 3, mt: 2 }}>
        <Typography variant="h6" gutterBottom>
          ⚙️ Configuración del Sistema
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Esta página permitirá configurar todos los aspectos del sistema.
        </Typography>
        <ul>
          <li>Configuración de red</li>
          <li>Configuración de cámaras</li>
          <li>Preferencias de usuario</li>
          <li>Configuración de protocolos</li>
          <li>Respaldos y restauración</li>
        </ul>
      </Paper>
    </Box>
  );
};

export default SettingsPage;
