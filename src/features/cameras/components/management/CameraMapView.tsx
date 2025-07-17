/**
 * 🎯 Camera Map View Component
 * Vista de mapa para mostrar ubicación de cámaras (placeholder)
 */

import React from 'react';
import {
  Box,
  Paper,
  Typography,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Map as MapIcon,
} from '@mui/icons-material';
import { CameraResponse } from '../../../../types/camera.types.v2';

interface CameraMapViewProps {
  cameras: CameraResponse[];
  isLoading: boolean;
  selectedCameras: Set<string>;
  onSelectCamera: (cameraId: string, selected: boolean) => void;
}

export const CameraMapView: React.FC<CameraMapViewProps> = ({
  cameras,
  isLoading,
  selectedCameras,
  onSelectCamera,
}) => {
  const theme = useTheme();

  // TODO: Implementar integración con librería de mapas (Leaflet, Google Maps, etc.)
  
  return (
    <Paper
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: alpha(theme.palette.primary.main, 0.02),
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 2,
          p: 4,
        }}
      >
        <Box
          sx={{
            width: 100,
            height: 100,
            borderRadius: '50%',
            bgcolor: alpha(theme.palette.primary.main, 0.1),
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <MapIcon sx={{ fontSize: 60, color: 'primary.main' }} />
        </Box>
        
        <Typography variant="h6" color="text.secondary">
          Vista de Mapa
        </Typography>
        
        <Typography 
          variant="body2" 
          color="text.secondary" 
          align="center"
          sx={{ maxWidth: 400 }}
        >
          La vista de mapa estará disponible próximamente. 
          Permitirá visualizar la ubicación geográfica de las cámaras 
          y su estado en tiempo real.
        </Typography>
        
        <Typography variant="caption" color="text.secondary">
          {cameras.filter(cam => cam.location).length} cámaras con ubicación definida
        </Typography>
      </Box>
    </Paper>
  );
};