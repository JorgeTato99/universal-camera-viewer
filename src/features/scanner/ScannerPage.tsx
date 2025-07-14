import React from "react";
import { Box, Typography, Paper } from "@mui/material";

const ScannerPage: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Escáner de Red
      </Typography>

      <Paper sx={{ p: 3, mt: 2 }}>
        <Typography variant="h6" gutterBottom>
          🔍 Descubrimiento de Cámaras
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Esta página permitirá escanear la red para encontrar cámaras IP
          automáticamente.
        </Typography>
        <ul>
          <li>Escaneo de rangos de IP</li>
          <li>Detección de protocolos</li>
          <li>Configuración de escaneo</li>
          <li>Resultados en tiempo real</li>
        </ul>
      </Paper>
    </Box>
  );
};

export default ScannerPage;
