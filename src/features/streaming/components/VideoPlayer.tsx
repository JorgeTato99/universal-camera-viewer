/**
 * 🎥 Video Player Component - Universal Camera Viewer
 * Componente para mostrar video streaming en tiempo real
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  Box,
  IconButton,
  Typography,
  Tooltip,
  CircularProgress,
  Chip,
  Paper,
  Fade,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
  VolumeOff as MuteIcon,
  VolumeUp as UnmuteIcon,
  PhotoCamera as SnapshotIcon,
  Settings as SettingsIcon,
  SignalCellularAlt as SignalIcon,
  Circle as RecordIcon,
} from '@mui/icons-material';
import { useStreamingStore } from '../../../stores/streamingStore';
import { streamingService } from '../../../services/python/streamingService';
import { colorTokens } from '../../../design-system/tokens';

interface VideoPlayerProps {
  cameraId: string;
  width?: string | number;
  height?: string | number;
  autoPlay?: boolean;
  showControls?: boolean;
  onSnapshot?: (imageData: string) => void;
  onError?: (error: string) => void;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  cameraId,
  width = '100%',
  height = 'auto',
  autoPlay = true,
  showControls = true,
  onSnapshot,
  onError,
}) => {
  const imgRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [showOverlay, setShowOverlay] = useState(true);
  const [currentFrame, setCurrentFrame] = useState<string | null>(null);
  const [metrics, setMetrics] = useState({
    fps: 0,
    latency: 0,
    quality: 'medium',
    frameCount: 0,
  });

  const {
    activeSessions,
    startStream,
    stopStream,
    updateFrame,
    updateStreamMetrics,
  } = useStreamingStore();

  const session = activeSessions.get(cameraId);

  // Ocultar overlay después de 3 segundos de inactividad
  useEffect(() => {
    let timeoutId: NodeJS.Timeout;
    
    const handleMouseMove = () => {
      setShowOverlay(true);
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => setShowOverlay(false), 3000);
    };

    const container = containerRef.current;
    if (container && isPlaying) {
      container.addEventListener('mousemove', handleMouseMove);
      timeoutId = setTimeout(() => setShowOverlay(false), 3000);
    }

    return () => {
      if (container) {
        container.removeEventListener('mousemove', handleMouseMove);
      }
      clearTimeout(timeoutId);
    };
  }, [isPlaying]);

  // Conectar al WebSocket
  const handleConnect = useCallback(async () => {
    try {
      setIsConnecting(true);
      
      // Iniciar sesión en el store
      startStream(cameraId);
      
      // Conectar WebSocket
      await streamingService.connect(cameraId);
      
      // Registrar callbacks
      const unsubscribeFrame = streamingService.onFrame((frameData) => {
        setCurrentFrame(frameData.data);
        setMetrics(prev => ({
          ...prev,
          frameCount: prev.frameCount + 1,
        }));
        
        // Actualizar store
        updateFrame(cameraId, frameData);
      });
      
      const unsubscribeStatus = streamingService.onStatus((status, data) => {
        console.log('Estado del stream:', status, data);
      });
      
      const unsubscribeError = streamingService.onError((error) => {
        console.error('Error en stream:', error);
        onError?.(error);
        handleDisconnect();
      });
      
      // Iniciar streaming
      await streamingService.startStream({
        quality: 'medium',
        fps: 30,
        format: 'jpeg',
      });
      
      setIsPlaying(true);
      setIsConnecting(false);
      
      // Limpiar al desmontar
      return () => {
        unsubscribeFrame();
        unsubscribeStatus();
        unsubscribeError();
      };
    } catch (error) {
      console.error('Error conectando:', error);
      setIsConnecting(false);
      onError?.(error instanceof Error ? error.message : 'Error de conexión');
    }
  }, [cameraId, startStream, updateFrame, onError]);

  // Desconectar del WebSocket
  const handleDisconnect = useCallback(async () => {
    try {
      await streamingService.stopStream();
      streamingService.disconnect();
      stopStream(cameraId);
      setIsPlaying(false);
      setCurrentFrame(null);
    } catch (error) {
      console.error('Error desconectando:', error);
    }
  }, [cameraId, stopStream]);

  // Play/Pause
  const togglePlayPause = useCallback(async () => {
    if (isPlaying) {
      await handleDisconnect();
    } else {
      await handleConnect();
    }
  }, [isPlaying, handleConnect, handleDisconnect]);

  // Capturar snapshot
  const handleSnapshot = useCallback(() => {
    if (currentFrame && onSnapshot) {
      onSnapshot(currentFrame);
    }
  }, [currentFrame, onSnapshot]);

  // Fullscreen
  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement && containerRef.current) {
      containerRef.current.requestFullscreen();
      setIsFullscreen(true);
    } else if (document.exitFullscreen) {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  // Auto-play cuando el componente se monta
  useEffect(() => {
    let mounted = true;
    let timeoutId: NodeJS.Timeout;
    
    // Retrasar el auto-play para evitar problemas con StrictMode
    if (autoPlay && !isPlaying && !isConnecting) {
      timeoutId = setTimeout(() => {
        if (mounted && !streamingService.isConnected()) {
          handleConnect();
        }
      }, 100);
    }
    
    return () => {
      mounted = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      // Solo desconectar si el componente realmente está siendo desmontado
      // y no es un re-render de StrictMode
      if (isPlaying && !document.querySelector(`[data-camera-id="${cameraId}"]`)) {
        handleDisconnect();
      }
    };
  }, []); // Solo ejecutar al montar

  // Calcular métricas
  useEffect(() => {
    if (streamingService.isConnected()) {
      const interval = setInterval(() => {
        const metrics = streamingService.getMetrics();
        setMetrics(prev => ({
          ...prev,
          fps: metrics.fps,
          latency: Math.round(Math.random() * 50 + 20), // Mock latency
        }));
      }, 1000);
      
      return () => clearInterval(interval);
    }
  }, [isPlaying]);

  return (
    <Box
      ref={containerRef}
      data-camera-id={cameraId}
      sx={{
        position: 'relative',
        width,
        height,
        backgroundColor: '#000',
        borderRadius: 1,
        overflow: 'hidden',
        cursor: showOverlay ? 'default' : 'none',
      }}
    >
      {/* Video/Image Display */}
      {currentFrame ? (
        <img
          ref={imgRef}
          src={`data:image/jpeg;base64,${currentFrame}`}
          alt="Video Stream"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'contain',
          }}
        />
      ) : (
        <Box
          sx={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'text.secondary',
          }}
        >
          {isConnecting ? (
            <Box sx={{ textAlign: 'center' }}>
              <CircularProgress size={48} />
              <Typography variant="body2" sx={{ mt: 2 }}>
                Conectando...
              </Typography>
            </Box>
          ) : (
            <Typography variant="body1">
              Sin señal de video
            </Typography>
          )}
        </Box>
      )}

      {/* Status Overlay */}
      <Fade in={showOverlay}>
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            p: 2,
            background: 'linear-gradient(to bottom, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0) 100%)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
          }}
        >
          {/* Camera Info */}
          <Box>
            <Typography variant="h6" sx={{ color: '#fff', fontSize: '1rem' }}>
              Cámara {cameraId}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
              <Chip
                size="small"
                icon={<RecordIcon sx={{ fontSize: '0.8rem' }} />}
                label={isPlaying ? 'EN VIVO' : 'DETENIDO'}
                sx={{
                  backgroundColor: isPlaying ? colorTokens.status.connected : colorTokens.status.disconnected,
                  color: '#fff',
                  fontSize: '0.7rem',
                }}
              />
              {isPlaying && (
                <>
                  <Chip
                    size="small"
                    label={`${metrics.fps} FPS`}
                    sx={{
                      backgroundColor: 'rgba(255,255,255,0.2)',
                      color: '#fff',
                      fontSize: '0.7rem',
                    }}
                  />
                  <Chip
                    size="small"
                    icon={<SignalIcon sx={{ fontSize: '0.8rem' }} />}
                    label={`${metrics.latency}ms`}
                    sx={{
                      backgroundColor: 'rgba(255,255,255,0.2)',
                      color: '#fff',
                      fontSize: '0.7rem',
                    }}
                  />
                </>
              )}
            </Box>
          </Box>

          {/* Settings */}
          <IconButton
            size="small"
            sx={{ color: '#fff' }}
            onClick={() => console.log('Settings')}
          >
            <SettingsIcon />
          </IconButton>
        </Box>
      </Fade>

      {/* Controls Overlay */}
      {showControls && (
        <Fade in={showOverlay}>
          <Paper
            sx={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              p: 1,
              background: 'rgba(0,0,0,0.8)',
              backdropFilter: 'blur(10px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 1,
            }}
          >
            {/* Play/Pause */}
            <Tooltip title={isPlaying ? 'Pausar' : 'Reproducir'}>
              <IconButton
                size="small"
                onClick={togglePlayPause}
                disabled={isConnecting}
                sx={{ color: '#fff' }}
              >
                {isPlaying ? <PauseIcon /> : <PlayIcon />}
              </IconButton>
            </Tooltip>

            {/* Stop */}
            <Tooltip title="Detener">
              <IconButton
                size="small"
                onClick={handleDisconnect}
                disabled={!isPlaying}
                sx={{ color: '#fff' }}
              >
                <StopIcon />
              </IconButton>
            </Tooltip>

            {/* Separator */}
            <Box sx={{ width: 1, height: 24, backgroundColor: 'rgba(255,255,255,0.2)' }} />

            {/* Mute/Unmute */}
            <Tooltip title={isMuted ? 'Activar sonido' : 'Silenciar'}>
              <IconButton
                size="small"
                onClick={() => setIsMuted(!isMuted)}
                sx={{ color: '#fff' }}
              >
                {isMuted ? <MuteIcon /> : <UnmuteIcon />}
              </IconButton>
            </Tooltip>

            {/* Snapshot */}
            <Tooltip title="Capturar imagen">
              <IconButton
                size="small"
                onClick={handleSnapshot}
                disabled={!currentFrame}
                sx={{ color: '#fff' }}
              >
                <SnapshotIcon />
              </IconButton>
            </Tooltip>

            {/* Fullscreen */}
            <Tooltip title={isFullscreen ? 'Salir de pantalla completa' : 'Pantalla completa'}>
              <IconButton
                size="small"
                onClick={toggleFullscreen}
                sx={{ color: '#fff' }}
              >
                {isFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
              </IconButton>
            </Tooltip>
          </Paper>
        </Fade>
      )}
    </Box>
  );
};