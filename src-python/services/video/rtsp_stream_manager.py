"""
Stream Manager específico para protocolo RTSP.

Implementa la captura de video desde streams RTSP usando OpenCV.
"""

import cv2
import numpy as np
from typing import Optional
import asyncio
import time

from services.video.stream_manager import StreamManager
from models.streaming import StreamStatus


class RTSPStreamManager(StreamManager):
    """
    Stream Manager para protocolo RTSP.
    
    Utiliza OpenCV VideoCapture para conectar y capturar
    frames desde streams RTSP.
    """
    
    async def _initialize_connection(self) -> None:
        """Inicializa la conexión RTSP."""
        try:
            # Construir URL RTSP
            rtsp_url = self._build_rtsp_url()
            
            self.logger.info(f"Conectando a RTSP: {self._sanitize_url(rtsp_url)}")
            
            # Crear VideoCapture
            self._connection = cv2.VideoCapture(rtsp_url)
            
            # Configurar buffer para reducir latencia
            self._connection.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Configurar timeout (si está soportado)
            if hasattr(cv2, 'CAP_PROP_OPEN_TIMEOUT_MSEC'):
                self._connection.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
            if hasattr(cv2, 'CAP_PROP_READ_TIMEOUT_MSEC'):
                self._connection.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)
            
            # Verificar que se abrió correctamente
            if not self._connection.isOpened():
                raise ConnectionError("No se pudo abrir el stream RTSP")
            
            # Obtener información del stream
            width = int(self._connection.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self._connection.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(self._connection.get(cv2.CAP_PROP_FPS))
            
            self.logger.info(f"Stream RTSP conectado: {width}x{height} @ {fps}fps")
            
            # Actualizar metadata
            self.stream_model.metadata.update({
                'width': width,
                'height': height,
                'native_fps': fps,
                'codec': self._get_codec_info()
            })
            
        except Exception as e:
            self.logger.error(f"Error inicializando conexión RTSP: {e}")
            raise
    
    async def _validate_stream(self) -> None:
        """Valida que el stream RTSP es válido."""
        if not self._connection or not self._connection.isOpened():
            raise ValueError("Conexión RTSP no válida")
        
        # Intentar leer un frame de prueba
        ret, frame = self._connection.read()
        if not ret or frame is None:
            raise ValueError("No se puede leer frames del stream RTSP")
        
        self.logger.debug("Stream RTSP validado correctamente")
    
    def _capture_frame(self) -> Optional[np.ndarray]:
        """
        Captura un frame del stream RTSP.
        
        Returns:
            Frame como numpy array o None si falla
        """
        if not self._connection or not self._connection.isOpened():
            return None
        
        try:
            ret, frame = self._connection.read()
            
            if ret and frame is not None:
                return frame
            else:
                # Intentar reconectar si falla
                if self._is_streaming:
                    self._attempt_reconnect()
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturando frame RTSP: {e}")
            return None
    
    async def _close_connection(self) -> None:
        """Cierra la conexión RTSP."""
        if self._connection:
            self._connection.release()
            self._connection = None
            self.logger.debug("Conexión RTSP cerrada")
    
    def _build_rtsp_url(self) -> str:
        """
        Construye la URL RTSP desde la configuración.
        
        Returns:
            URL RTSP completa
        """
        config = self.connection_config
        
        # Si ya hay una URL completa, usarla
        if hasattr(config, 'rtsp_url') and config.rtsp_url:
            return config.rtsp_url
        
        # Construir URL desde componentes
        if config.username and config.password:
            auth = f"{config.username}:{config.password}@"
        else:
            auth = ""
        
        # Puerto por defecto RTSP
        port = config.port or 554
        
        # Path por defecto según marca
        if hasattr(config, 'rtsp_path') and config.rtsp_path:
            path = config.rtsp_path
        elif hasattr(config, 'brand') and config.brand:
            # Paths específicos por marca
            brand_paths = {
                'dahua': '/cam/realmonitor?channel=1&subtype=0',
                'tp-link': '/stream1',
                'steren': '/Streaming/Channels/101',
                'hikvision': '/Streaming/Channels/101',
                'generic': '/stream1'
            }
            path = brand_paths.get(config.brand.lower(), '/stream1')
        else:
            # Si no hay información de marca, usar path de Dahua por defecto
            # ya que es la cámara que estamos probando
            path = '/cam/realmonitor?channel=1&subtype=0'
        
        # Construir URL completa
        rtsp_url = f"rtsp://{auth}{config.ip}:{port}{path}"
        
        self.logger.debug(f"URL RTSP construida: {self._sanitize_url(rtsp_url)}")
        self.logger.debug(f"  - IP: {config.ip}")
        self.logger.debug(f"  - Puerto: {port}")
        self.logger.debug(f"  - Path: {path}")
        self.logger.debug(f"  - Marca: {getattr(config, 'brand', 'unknown')}")
        
        return rtsp_url
    
    def _sanitize_url(self, url: str) -> str:
        """
        Sanitiza la URL para logging (oculta credenciales).
        
        Args:
            url: URL completa
            
        Returns:
            URL sin credenciales
        """
        if '@' in url:
            # Ocultar credenciales
            parts = url.split('@')
            protocol_part = parts[0].split('://')
            if len(protocol_part) > 1:
                return f"{protocol_part[0]}://***:***@{parts[1]}"
        return url
    
    def _get_codec_info(self) -> str:
        """Obtiene información del codec del stream."""
        if not self._connection:
            return "unknown"
        
        # Obtener fourcc
        fourcc = int(self._connection.get(cv2.CAP_PROP_FOURCC))
        
        # Convertir a string
        if fourcc > 0:
            codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            return codec.strip()
        
        return "unknown"
    
    def _attempt_reconnect(self) -> None:
        """Intenta reconectar al stream RTSP."""
        self.logger.warning("Intentando reconectar al stream RTSP...")
        
        try:
            # Cerrar conexión actual
            if self._connection:
                self._connection.release()
            
            # Esperar un momento
            time.sleep(1)
            
            # Reintentar conexión
            rtsp_url = self._build_rtsp_url()
            self._connection = cv2.VideoCapture(rtsp_url)
            self._connection.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if self._connection.isOpened():
                self.logger.info("Reconexión RTSP exitosa")
                self.stream_model.reconnect_attempts += 1
            else:
                self.logger.error("Fallo la reconexión RTSP")
                
        except Exception as e:
            self.logger.error(f"Error en reconexión RTSP: {e}")