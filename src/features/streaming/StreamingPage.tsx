import React from "react";
import { Box, Typography, Paper } from "@mui/material";
import { useParams } from "react-router-dom";

const StreamingPage: React.FC = () => {
  const { cameraId } = useParams<{ cameraId: string }>();

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Vista de Streaming
      </Typography>

      <Paper sx={{ p: 3, mt: 2 }}>
        <Typography variant="h6" gutterBottom>
          📺 Vista en Tiempo Real
        </Typography>
        {cameraId && (
          <Typography variant="body2" color="primary" gutterBottom>
            Cámara ID: {cameraId}
          </Typography>
        )}
        <Typography variant="body1" color="text.secondary">
          Esta página mostrará el streaming en tiempo real de la cámara
          seleccionada.
        </Typography>
        <ul>
          <li>Video en tiempo real</li>
          <li>Controles de reproducción</li>
          <li>Captura de screenshots</li>
          <li>Controles PTZ</li>
          <li>Métricas de streaming</li>
        </ul>
      </Paper>
    </Box>
  );
};

export default StreamingPage;
