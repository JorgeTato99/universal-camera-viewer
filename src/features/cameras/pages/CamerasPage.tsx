/**
 * 🎯 Cameras Page - Universal Camera Viewer
 * Página principal de gestión de cámaras con nuevo design system
 */

import React from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  IconButton,
  Divider,
} from "@mui/material";
import {
  Add as AddIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Videocam as VideocamIcon,
  Settings as SettingsIcon,
  PhotoCamera as PhotoCameraIcon,
  PlayArrow as PlayArrowIcon,
} from "@mui/icons-material";
import {
  cardStyles,
  buttonStyles,
  statusStyles,
} from "../../../design-system/components";
import { colorTokens } from "../../../design-system/tokens";
import { useCameraStore } from "../../../stores";
import { Camera } from "../../../types/camera.types";

export const CamerasPage: React.FC = () => {
  const { cameras, isLoading } = useCameraStore();

  const handleAddCamera = () => {
    console.log("Agregar nueva cámara");
  };

  const handleScanNetwork = () => {
    console.log("Escanear red");
  };

  const handleRefresh = () => {
    console.log("Actualizar lista");
  };

  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      {/* Header con título y controles */}
      <Box
        sx={{
          p: 3,
          borderBottom: `1px solid ${colorTokens.neutral[200]}`,
          backgroundColor: colorTokens.background.paper,
          flexShrink: 0,
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            mb: 2,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <VideocamIcon
              sx={{ color: colorTokens.primary[500], fontSize: 28 }}
            />
            <Typography
              variant="h4"
              sx={{ fontWeight: 600, color: colorTokens.neutral[900] }}
            >
              Gestión de Cámaras
            </Typography>
          </Box>

          <Box sx={{ display: "flex", gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={handleRefresh}
              sx={buttonStyles.outlined}
            >
              Actualizar
            </Button>
            <Button
              variant="outlined"
              startIcon={<SearchIcon />}
              onClick={handleScanNetwork}
              sx={buttonStyles.outlined}
            >
              Escanear Red
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleAddCamera}
              sx={buttonStyles.primary}
            >
              Agregar Cámara
            </Button>
          </Box>
        </Box>

        {/* Estadísticas rápidas */}
        <Box sx={{ display: "flex", gap: 2 }}>
          <Chip
            label="3 Conectadas"
            sx={{
              ...statusStyles.connected,
              fontSize: "12px",
            }}
          />
          <Chip
            label="1 Conectando"
            sx={{
              ...statusStyles.connecting,
              fontSize: "12px",
            }}
          />
          <Chip
            label="2 Desconectadas"
            sx={{
              ...statusStyles.disconnected,
              fontSize: "12px",
            }}
          />
        </Box>
      </Box>

      {/* Contenido principal */}
      <Box sx={{ flex: 1, overflow: "auto", p: 3 }}>
        {cameras.length === 0 ? (
          // Estado vacío
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              minHeight: "400px",
              textAlign: "center",
            }}
          >
            <VideocamIcon
              sx={{
                fontSize: 64,
                color: colorTokens.neutral[400],
                mb: 2,
              }}
            />
            <Typography
              variant="h5"
              sx={{
                mb: 1,
                color: colorTokens.neutral[600],
                fontWeight: 500,
              }}
            >
              No hay cámaras configuradas
            </Typography>
            <Typography
              variant="body2"
              sx={{
                mb: 3,
                color: colorTokens.neutral[500],
                maxWidth: "400px",
              }}
            >
              Comienza agregando cámaras manualmente o utiliza la función de
              escaneo automático para descubrir dispositivos en tu red.
            </Typography>
            <Box sx={{ display: "flex", gap: 2 }}>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleAddCamera}
                sx={buttonStyles.primary}
              >
                Agregar Cámara
              </Button>
              <Button
                variant="outlined"
                startIcon={<SearchIcon />}
                onClick={handleScanNetwork}
                sx={buttonStyles.outlined}
              >
                Escanear Red
              </Button>
            </Box>
          </Box>
        ) : (
          // Lista de cámaras
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
              gap: 3,
              width: "100%",
            }}
          >
            {cameras.map((camera: Camera) => (
              <Card key={camera.camera_id} sx={cardStyles.camera}>
                <CardContent>
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      mb: 2,
                    }}
                  >
                    <Typography
                      variant="h6"
                      sx={{ fontWeight: 500, fontSize: "1rem" }}
                    >
                      {camera.display_name}
                    </Typography>
                    <Chip
                      label={camera.status}
                      size="small"
                      sx={
                        statusStyles[
                          camera.status as keyof typeof statusStyles
                        ] || statusStyles.unavailable
                      }
                    />
                  </Box>

                  <Typography
                    variant="body2"
                    sx={{
                      color: colorTokens.neutral[600],
                      fontFamily: "monospace",
                      mb: 2,
                    }}
                  >
                    {camera.connection_config.ip}
                  </Typography>

                  <Divider sx={{ my: 2 }} />

                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <Box sx={{ display: "flex", gap: 1 }}>
                      <IconButton
                        size="small"
                        sx={{ color: colorTokens.primary[500] }}
                      >
                        <PlayArrowIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        sx={{ color: colorTokens.neutral[600] }}
                      >
                        <PhotoCameraIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        sx={{ color: colorTokens.neutral[600] }}
                      >
                        <SettingsIcon />
                      </IconButton>
                    </Box>
                    <Typography
                      variant="caption"
                      sx={{ color: colorTokens.neutral[500] }}
                    >
                      {camera.current_protocol || "N/A"}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            ))}
          </Box>
        )}
      </Box>
    </Box>
  );
};
