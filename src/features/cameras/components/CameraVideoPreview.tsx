/**
 * 🎬 Camera Video Preview Component
 * Componente para mostrar preview de video en las tarjetas de cámara
 */

import React, { useState, useEffect, useRef } from "react";
import { Box, CircularProgress, Typography } from "@mui/material";
import { Videocam as VideocamIcon } from "@mui/icons-material";
import { colorTokens } from "../../../design-system/tokens";
import { streamingService } from "../../../services/python/streamingService";

interface CameraVideoPreviewProps {
  cameraId: string;
  isConnected: boolean;
  aspectRatio?: string;
  height?: string;
  onError?: (error: string) => void;
  onMetricsUpdate?: (metrics: { fps: number; latency: number; isStreaming: boolean }) => void;
}

export const CameraVideoPreview: React.FC<CameraVideoPreviewProps> = ({
  cameraId,
  isConnected,
  onMetricsUpdate,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [currentFrame, setCurrentFrame] = useState<string | null>(null);
  const imgRef1 = useRef<HTMLImageElement>(null);
  const imgRef2 = useRef<HTMLImageElement>(null);
  const [activeImg, setActiveImg] = useState(1);

  // Mostrar video cuando la cámara esté conectada
  useEffect(() => {
    if (isConnected) {
      setIsLoading(true);
      
      // Suscribirse a los frames del WebSocket
      const handleFrame = (frameData: any) => {
        if (frameData.camera_id === cameraId) {
          const newSrc = `data:image/jpeg;base64,${frameData.data}`;
          
          // Double buffering: alternar entre dos imágenes para evitar parpadeo
          if (activeImg === 1) {
            if (imgRef2.current) {
              imgRef2.current.src = newSrc;
              imgRef2.current.style.display = 'block';
              if (imgRef1.current) imgRef1.current.style.display = 'none';
              setActiveImg(2);
            }
          } else {
            if (imgRef1.current) {
              imgRef1.current.src = newSrc;
              imgRef1.current.style.display = 'block';
              if (imgRef2.current) imgRef2.current.style.display = 'none';
              setActiveImg(1);
            }
          }
          
          if (!currentFrame) {
            setCurrentFrame(newSrc);
          }
          
          setIsLoading(false);
          
          // Actualizar métricas si están disponibles
          if (frameData.metrics && onMetricsUpdate) {
            onMetricsUpdate({
              fps: frameData.metrics.fps || 0,
              latency: frameData.metrics.latency || 0,
              isStreaming: true,
            });
          }
        }
      };
      
      // Registrar callback para frames
      const unsubscribe = streamingService.onFrame(cameraId, handleFrame);
      
      return () => {
        // Desregistrar callback al desmontar
        unsubscribe();
      };
    } else {
      setIsLoading(false);
      setCurrentFrame(null);
      // Notificar que el streaming se detuvo
      if (onMetricsUpdate) {
        onMetricsUpdate({
          fps: 0,
          latency: 0,
          isStreaming: false,
        });
      }
    }
  }, [isConnected, cameraId, onMetricsUpdate]);

  if (!isConnected) {
    return (
      <Box
        sx={{
          width: "100%",
          height: "100%",
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
          height: "100%",
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

  // Mostrar el video cuando esté conectado
  return (
    <Box
      sx={{
        width: "100%",
        height: "100%",
        backgroundColor: "#000",
        borderRadius: "6px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        border: (theme) => `1px solid ${theme.palette.divider}`,
        position: "relative",
        overflow: "hidden",
      }}
    >
      {currentFrame ? (
        <>
          <img
            ref={imgRef1}
            src={currentFrame}
            alt={`Camera ${cameraId}`}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
              objectFit: "cover",
              display: activeImg === 1 ? 'block' : 'none',
            }}
          />
          <img
            ref={imgRef2}
            alt={`Camera ${cameraId}`}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
              objectFit: "cover",
              display: activeImg === 2 ? 'block' : 'none',
            }}
          />
        </>
      ) : (
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 1,
            color: "#fff",
          }}
        >
          <CircularProgress size={30} sx={{ color: "#fff" }} />
          <Typography variant="caption" sx={{ fontSize: "0.8rem" }}>
            Cargando video...
          </Typography>
        </Box>
      )}
    </Box>
  );
};
