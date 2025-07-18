/**
 * 🎬 Video Stream Component - Optimized for WebSocket Streaming
 * Componente optimizado para streaming sin parpadeo usando Canvas
 */

import React, { useEffect, useRef, useCallback } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { Videocam as VideocamIcon } from '@mui/icons-material';
import { colorTokens } from '../../../design-system/tokens';
import { streamingService } from '../../../services/python/streamingService';

interface StreamMetrics {
  fps: number;
  latency: number;
  isStreaming: boolean;
  latencyType?: 'real' | 'simulated';
  avgFps?: number;
  avgLatency?: number;
  healthScore?: number;
  rtt?: number;
  avgRtt?: number;
  minRtt?: number;
  maxRtt?: number;
}

interface VideoStreamProps {
  cameraId: string;
  isConnected: boolean;
  aspectRatio?: string;
  height?: string;
  onError?: (error: string) => void;
  onMetricsUpdate?: (metrics: StreamMetrics) => void;
}

export const VideoStream: React.FC<VideoStreamProps> = React.memo(({
  cameraId,
  isConnected,
  aspectRatio = '16:9',
  height = '100%',
  onError,
  onMetricsUpdate,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement>(new Image());
  const blobUrlRef = useRef<string | null>(null);
  const animationIdRef = useRef<number>(0);
  const isLoadingRef = useRef(true);
  const [isFirstFrame, setIsFirstFrame] = React.useState(true);
  
  // Para throttling de métricas
  const lastMetricsUpdateRef = useRef<number>(0);
  const latestMetricsRef = useRef<StreamMetrics | null>(null);
  const rttInfoRef = useRef<{ current: number; average: number; min: number; max: number } | null>(null);

  // Convertir base64 a blob para mejor performance
  const base64ToBlob = useCallback((base64: string): Blob => {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: 'image/jpeg' });
  }, []);

  // Render loop con requestAnimationFrame
  const renderFrame = useCallback(() => {
    const canvas = canvasRef.current;
    const image = imageRef.current;
    
    if (!canvas || !image) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Solo dibujar si la imagen está completamente cargada
    if (image.complete && image.naturalHeight !== 0) {
      // Ajustar el tamaño del canvas al tamaño de la imagen si es necesario
      if (canvas.width !== image.naturalWidth || canvas.height !== image.naturalHeight) {
        canvas.width = image.naturalWidth;
        canvas.height = image.naturalHeight;
      }
      
      // Dibujar la imagen en el canvas
      ctx.drawImage(image, 0, 0);
      
      // Ocultar el loading después del primer frame
      if (isLoadingRef.current) {
        isLoadingRef.current = false;
        setIsFirstFrame(false);
      }
    }
    
    // Continuar el loop de animación
    animationIdRef.current = requestAnimationFrame(renderFrame);
  }, []);

  // Manejar actualizaciones de RTT
  const handleRTTUpdate = useCallback((rtt: number) => {
    // Obtener información completa de RTT
    const rttInfo = streamingService.getRTTInfo(cameraId);
    if (rttInfo) {
      rttInfoRef.current = rttInfo;
    }
  }, [cameraId]);

  // Manejar frames del WebSocket
  const handleFrame = useCallback((frameData: any) => {
    if (frameData.camera_id !== cameraId) return;
    
    try {
      // Convertir base64 a blob
      const blob = base64ToBlob(frameData.data);
      
      // Limpiar URL anterior para evitar memory leaks
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current);
      }
      
      // Crear nueva URL del blob
      blobUrlRef.current = URL.createObjectURL(blob);
      
      // Crear nueva imagen si no existe
      if (!imageRef.current) {
        imageRef.current = new Image();
      }
      
      // Actualizar la fuente de la imagen
      imageRef.current.src = blobUrlRef.current;
      
      // Actualizar métricas con throttling (máximo 1 vez por segundo)
      if (frameData.metrics) {
        const metrics: StreamMetrics = {
          fps: frameData.metrics.fps || 0,
          latency: frameData.metrics.latency || 0,
          isStreaming: true,
          latencyType: frameData.metrics.latency_type,
          avgFps: frameData.metrics.avg_fps,
          avgLatency: frameData.metrics.avg_latency,
          healthScore: frameData.metrics.health_score,
          // Incluir información de RTT si está disponible
          rtt: rttInfoRef.current?.current || 0,
          avgRtt: rttInfoRef.current?.average || 0,
          minRtt: rttInfoRef.current?.min || 0,
          maxRtt: rttInfoRef.current?.max || 0,
        };
        
        // Guardar las métricas más recientes
        latestMetricsRef.current = metrics;
        
        // Solo actualizar si ha pasado al menos 1 segundo desde la última actualización
        const now = Date.now();
        if (now - lastMetricsUpdateRef.current >= 1000) {
          lastMetricsUpdateRef.current = now;
          if (onMetricsUpdate) {
            onMetricsUpdate(metrics);
          }
        }
      }
    } catch (error) {
      console.error('Error procesando frame:', error);
      if (onError) {
        onError('Error al procesar frame de video');
      }
    }
  }, [cameraId, base64ToBlob, onMetricsUpdate, onError]);

  // Log solo cuando cambia isConnected
  useEffect(() => {
    console.log(`[VideoStream ${cameraId}] isConnected changed to:`, isConnected);
  }, [cameraId, isConnected]);

  // Efecto para actualizar métricas periódicamente
  useEffect(() => {
    if (!isConnected || !onMetricsUpdate) return;
    
    // Intervalo para asegurar actualización de métricas cada segundo
    const metricsInterval = setInterval(() => {
      if (latestMetricsRef.current) {
        onMetricsUpdate(latestMetricsRef.current);
      }
    }, 1000);
    
    return () => clearInterval(metricsInterval);
  }, [isConnected, onMetricsUpdate]);

  // Efecto principal para manejar streaming
  useEffect(() => {
    if (!isConnected) {
      // Limpiar cuando se desconecta
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current);
        blobUrlRef.current = null;
      }
      if (imageRef.current) {
        imageRef.current.src = '';
      }
      isLoadingRef.current = true;
      setIsFirstFrame(true);
      
      // Resetear refs de métricas
      lastMetricsUpdateRef.current = 0;
      latestMetricsRef.current = null;
      
      // Notificar que el streaming se detuvo
      if (onMetricsUpdate) {
        onMetricsUpdate({
          fps: 0,
          latency: 0,
          isStreaming: false,
          latencyType: 'simulated',
          avgFps: 0,
          avgLatency: 0,
          healthScore: 0,
        });
      }
      return;
    }

    // Inicializar cuando se conecta
    isLoadingRef.current = true;
    
    // Crear imagen si no existe
    if (!imageRef.current) {
      imageRef.current = new Image();
    }
    
    // Iniciar render loop
    renderFrame();
    
    // Suscribirse a frames del WebSocket
    const unsubscribeFrame = streamingService.onFrame(cameraId, handleFrame);
    
    // Suscribirse a actualizaciones de RTT
    const unsubscribeRTT = streamingService.onRTT(cameraId, handleRTTUpdate);
    
    // Cleanup
    return () => {
      // Cancelar animation frame
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
      
      // Desuscribirse del WebSocket
      unsubscribeFrame();
      unsubscribeRTT();
      
      // Limpiar blob URL
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current);
        blobUrlRef.current = null;
      }
      
      // Limpiar imagen
      if (imageRef.current) {
        imageRef.current.src = '';
      }
      
      // Enviar las últimas métricas al desconectar
      if (latestMetricsRef.current && onMetricsUpdate) {
        onMetricsUpdate({
          ...latestMetricsRef.current,
          isStreaming: false,
        });
      }
    };
  }, [isConnected, cameraId, handleFrame, handleRTTUpdate, renderFrame, onMetricsUpdate]);

  // Si no está conectado, mostrar placeholder
  if (!isConnected) {
    return (
      <Box
        sx={{
          width: '100%',
          height: '100%',
          backgroundColor: (theme) =>
            theme.palette.mode === 'dark'
              ? colorTokens.background.dark
              : colorTokens.background.light,
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: (theme) => `1px solid ${theme.palette.divider}`,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 0.5,
            color: (theme) => theme.palette.text.disabled,
          }}
        >
          <VideocamIcon sx={{ fontSize: 32 }} />
          <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
            Sin conexión
          </Typography>
        </Box>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        width: '100%',
        height: '100%',
        backgroundColor: '#000',
        borderRadius: '6px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: (theme) => `1px solid ${theme.palette.divider}`,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Canvas para renderizar el video */}
      <canvas
        ref={canvasRef}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          display: isFirstFrame ? 'none' : 'block',
        }}
      />
      
      {/* Loading mientras carga el primer frame */}
      {isFirstFrame && (
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 1,
            color: '#fff',
          }}
        >
          <CircularProgress size={30} sx={{ color: '#fff' }} />
          <Typography variant="caption" sx={{ fontSize: '0.8rem' }}>
            Cargando video...
          </Typography>
        </Box>
      )}
    </Box>
  );
});

VideoStream.displayName = 'VideoStream';