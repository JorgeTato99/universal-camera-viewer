/**
 * 🎬 Camera Video Preview Component
 * Componente para mostrar preview de video en las tarjetas de cámara
 */

import React, { useState, useEffect } from "react";
import { Box, CircularProgress, Typography } from "@mui/material";
import { Videocam as VideocamIcon } from "@mui/icons-material";
import { VideoPlayer } from "../../streaming/components/VideoPlayer";
import { colorTokens } from "../../../design-system/tokens";

interface CameraVideoPreviewProps {
  cameraId: string;
  isConnected: boolean;
  aspectRatio?: string;
  height?: string;
  onError?: (error: string) => void;
}

export const CameraVideoPreview: React.FC<CameraVideoPreviewProps> = ({
  cameraId,
  isConnected,
  aspectRatio = "16:9",
  height = "180px",
  onError,
}) => {
  const [showVideo, setShowVideo] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Mostrar video cuando la cámara esté conectada
  useEffect(() => {
    if (isConnected) {
      setIsLoading(true);
      // Pequeño delay para evitar múltiples conexiones simultáneas
      const timer = setTimeout(() => {
        setShowVideo(true);
        setIsLoading(false);
      }, 500);

      return () => clearTimeout(timer);
    } else {
      setShowVideo(false);
      setIsLoading(false);
    }
  }, [isConnected]);

  if (!isConnected) {
    return (
      <Box
        sx={{
          width: "100%",
          aspectRatio,
          maxHeight: height,
          backgroundColor: (theme) =>
            theme.palette.mode === "dark"
              ? colorTokens.background.dark
              : colorTokens.background.light,
          borderRadius: "6px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          border: (theme) => `1px solid ${theme.palette.divider}`,
          position: "relative",
          overflow: "hidden",
        }}
      >
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 0.5,
            color: (theme) => theme.palette.text.disabled,
          }}
        >
          <VideocamIcon sx={{ fontSize: 32 }} />
          <Typography variant="caption" sx={{ fontSize: "0.7rem" }}>
            Sin conexión
          </Typography>
        </Box>
      </Box>
    );
  }

  if (isLoading) {
    return (
      <Box
        sx={{
          width: "100%",
          aspectRatio,
          maxHeight: height,
          backgroundColor: "#000",
          borderRadius: "6px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          border: (theme) => `1px solid ${theme.palette.divider}`,
        }}
      >
        <CircularProgress size={24} />
      </Box>
    );
  }

  if (showVideo) {
    return (
      <Box
        sx={{
          width: "100%",
          aspectRatio,
          maxHeight: height,
          borderRadius: "6px",
          overflow: "hidden",
          border: (theme) => `1px solid ${theme.palette.divider}`,
        }}
      >
        <VideoPlayer
          cameraId={cameraId}
          width="100%"
          height="100%"
          autoPlay={true}
          showControls={false}
          onError={onError}
        />
      </Box>
    );
  }

  return null;
};
