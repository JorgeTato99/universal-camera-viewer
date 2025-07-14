/**
 * 🎯 Camera Card Component - Universal Camera Viewer
 * Card individual para cada cámara
 */

import React from "react";
import { Box, Typography, Card, CardContent, Chip } from "@mui/material";
import { Videocam as VideocamIcon } from "@mui/icons-material";
import { cardStyles, statusStyles } from "../../../design-system/components";
import { colorTokens } from "../../../design-system/tokens";

interface CameraCardProps {
  cameraId: string;
  name?: string;
  status?: "connected" | "disconnected" | "connecting" | "error";
  aspectRatio?: "16:9" | "4:3";
}

export const CameraCard: React.FC<CameraCardProps> = ({
  cameraId,
  name = `Cámara ${cameraId}`,
  status = "disconnected",
  aspectRatio = "16:9",
}) => {
  const getStatusColor = () => {
    switch (status) {
      case "connected":
        return colorTokens.status.connected;
      case "connecting":
        return colorTokens.status.connecting;
      case "error":
        return colorTokens.status.error;
      default:
        return colorTokens.status.disconnected;
    }
  };

  const getStatusLabel = () => {
    switch (status) {
      case "connected":
        return "Conectada";
      case "connecting":
        return "Conectando...";
      case "error":
        return "Error";
      default:
        return "Desconectada";
    }
  };

  return (
    <Card sx={cardStyles.camera}>
      <CardContent sx={{ p: 1, "&:last-child": { pb: 1 } }}>
        {/* Header con nombre y estado */}
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: 1,
          }}
        >
          <Typography
            variant="h6"
            sx={{
              fontSize: "1rem",
              fontWeight: 500,
              color: (theme) => theme.palette.text.primary,
            }}
          >
            {name}
          </Typography>
          <Chip
            label={getStatusLabel()}
            size="small"
            sx={{
              backgroundColor: getStatusColor(),
              color: "#ffffff",
              fontSize: "0.75rem",
              fontWeight: 500,
            }}
          />
        </Box>

        {/* Área de video placeholder */}
        <Box
          sx={{
            width: "100%",
            aspectRatio: aspectRatio,
            backgroundColor: (theme) =>
              theme.palette.mode === "dark"
                ? colorTokens.background.dark
                : colorTokens.background.light,
            borderRadius: "4px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            border: (theme) => `1px solid ${theme.palette.divider}`,
            position: "relative",
            overflow: "hidden",
          }}
        >
          {status === "connected" ? (
            // Placeholder para video en vivo
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 1,
                color: (theme) => theme.palette.text.secondary,
              }}
            >
              <VideocamIcon sx={{ fontSize: 40 }} />
              <Typography variant="body2">Video en vivo</Typography>
            </Box>
          ) : (
            // Placeholder para cámara desconectada
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 1,
                color: (theme) => theme.palette.text.disabled,
              }}
            >
              <VideocamIcon sx={{ fontSize: 40 }} />
              <Typography variant="body2">Sin conexión</Typography>
            </Box>
          )}
        </Box>

        {/* Footer con información adicional */}
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mt: 1,
            pt: 1,
            borderTop: (theme) => `1px solid ${theme.palette.divider}`,
          }}
        >
          <Typography
            variant="caption"
            sx={{ color: (theme) => theme.palette.text.secondary }}
          >
            ID: {cameraId}
          </Typography>
          <Typography
            variant="caption"
            sx={{ color: (theme) => theme.palette.text.secondary }}
          >
            {aspectRatio}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};
