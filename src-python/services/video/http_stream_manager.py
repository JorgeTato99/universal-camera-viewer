"""
Stream Manager específico para protocolo HTTP/MJPEG.

Implementa la captura de video desde streams HTTP/MJPEG.
"""

import aiohttp
import cv2
import numpy as np
from typing import Optional
import asyncio
from io import BytesIO

from .stream_manager import StreamManager


class HTTPStreamManager(StreamManager):
    """
    Stream Manager para protocolo HTTP/MJPEG.
    
    Captura frames desde streams HTTP Motion JPEG.
    """
    
    def __init__(self, *args, **kwargs):
        """Inicializa el manager HTTP."""
        super().__init__(*args, **kwargs)
        self._session: Optional[aiohttp.ClientSession] = None
        self._stream_response: Optional[aiohttp.ClientResponse] = None
    
    async def _initialize_connection(self) -> None:
        """Inicializa la conexión HTTP."""
        try:
            # Construir URL HTTP
            http_url = self._build_http_url()
            
            self.logger.info(f"Conectando a stream HTTP: {self._sanitize_url(http_url)}")
            
            # Crear sesión HTTP
            auth = None
            if self.connection_config.username and self.connection_config.password:
                auth = aiohttp.BasicAuth(
                    self.connection_config.username,
                    self.connection_config.password
                )
            
            self._session = aiohttp.ClientSession(auth=auth)
            
            # Conectar al stream
            self._stream_response = await self._session.get(
                http_url,
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            if self._stream_response.status != 200:
                raise ConnectionError(f"HTTP error: {self._stream_response.status}")
            
            # Verificar content type
            content_type = self._stream_response.headers.get('Content-Type', '')
            if 'multipart/x-mixed-replace' not in content_type:
                self.logger.warning(f"Content-Type inesperado: {content_type}")
            
            self.logger.info("Stream HTTP conectado")
            
        except Exception as e:
            self.logger.error(f"Error inicializando conexión HTTP: {e}")
            raise
    
    async def _validate_stream(self) -> None:
        """Valida que el stream HTTP es válido."""
        if not self._stream_response:
            raise ValueError("Conexión HTTP no válida")
        
        # El stream MJPEG es válido si la respuesta está activa
        if self._stream_response.closed:
            raise ValueError("Stream HTTP cerrado")
        
        self.logger.debug("Stream HTTP validado")
    
    def _capture_frame(self) -> Optional[np.ndarray]:
        """
        Captura un frame del stream HTTP.
        
        Nota: HTTP streaming requiere manejo diferente,
        este es un placeholder simplificado.
        """
        # TODO: Implementar captura real desde MJPEG stream
        # Por ahora retorna None para evitar errores
        self.logger.warning("Captura HTTP no implementada completamente")
        return None
    
    async def _close_connection(self) -> None:
        """Cierra la conexión HTTP."""
        if self._stream_response:
            self._stream_response.close()
            
        if self._session:
            await self._session.close()
            
        self._stream_response = None
        self._session = None
        
        self.logger.debug("Conexión HTTP cerrada")
    
    def _build_http_url(self) -> str:
        """
        Construye la URL HTTP desde la configuración.
        
        Returns:
            URL HTTP completa
        """
        config = self.connection_config
        
        # Puerto por defecto HTTP
        port = config.port or 80
        
        # Path por defecto para MJPEG
        path = getattr(config, 'http_path', '/mjpeg/video.mjpeg')
        
        # Construir URL
        http_url = f"http://{config.ip}:{port}{path}"
        
        return http_url
    
    def _sanitize_url(self, url: str) -> str:
        """Sanitiza la URL para logging."""
        # Ocultar auth básica si existe
        if '@' in url:
            parts = url.split('@')
            protocol_part = parts[0].split('://')
            if len(protocol_part) > 1:
                return f"{protocol_part[0]}://***:***@{parts[1]}"
        return url