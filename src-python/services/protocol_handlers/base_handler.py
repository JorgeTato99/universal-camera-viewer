"""
BaseHandler - Clase base abstracta para manejadores de protocolos de cámara.

Combina funcionalidad de BaseConnection (src_old) con BaseProtocolHandler (src/services)
para mantener compatibilidad mientras se adopta la nueva arquitectura MVP.
"""

import asyncio
import cv2
import logging
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional, List, Callable

# Imports directos de la nueva arquitectura
from models import ConnectionConfig
from services.protocol_service import ConnectionState, ProtocolCapabilities, StreamingConfig


class BaseHandler(ABC):
    """
    Clase base abstracta para manejadores de protocolos de cámara.
    
    Combina la interfaz de BaseConnection (compatibilidad) con BaseProtocolHandler
    (nueva arquitectura async) para facilitar la migración gradual.
    
    Implementa:
    - Patrón Template Method 
    - Principios SOLID
    - Compatibilidad con API antigua
    - Nueva arquitectura async/await
    """
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa el handler base con compatibilidad dual.
        
        Soporte para múltiples formatos:
        - Nuevo: BaseHandler(config: ConnectionConfig, streaming_config: StreamingConfig)
        - Antiguo: BaseHandler(camera_ip: str, credentials: dict)
        """
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
        # Estado interno
        self._state = ConnectionState.DISCONNECTED
        self._connection_handle: Optional[Any] = None
        self._stream_handle: Optional[cv2.VideoCapture] = None
        self._last_frame_time: Optional[datetime] = None
        self._frame_count = 0
        self._fps = 0.0
        
        # Threading para streaming
        self._streaming_thread: Optional[asyncio.Task] = None
        self._streaming_active = False
        self._frame_callbacks: List[Callable[[Any], None]] = []
        
        # Procesamiento de argumentos (compatibilidad dual)
        self._parse_initialization_args(*args, **kwargs)
    
    def _parse_initialization_args(self, *args, **kwargs):
        """Parsea argumentos de inicialización con compatibilidad dual."""
        # NUEVA API: BaseHandler(config: ConnectionConfig, streaming_config: StreamingConfig)
        if len(args) >= 1 and hasattr(args[0], 'ip'):
            self.config = args[0]
            self.streaming_config = args[1] if len(args) > 1 else StreamingConfig()
            
            # Para compatibilidad
            self.camera_ip = self.config.ip
            self.credentials = {
                'username': self.config.username,
                'password': self.config.password
            }
            
        # ANTIGUA API: BaseHandler(camera_ip: str, credentials: dict)
        elif len(args) == 2 and isinstance(args[1], dict):
            self.camera_ip = args[0]
            self.credentials = args[1]
            
            # Crear config desde API antigua
            self.config = ConnectionConfig(
                ip=self.camera_ip,
                username=self.credentials.get('username', 'admin'),
                password=self.credentials.get('password', ''),
                rtsp_port=self.credentials.get('rtsp_port', 554),
                onvif_port=self.credentials.get('onvif_port', 80)
            )
            self.streaming_config = StreamingConfig()
            
        # LEGACY API: BaseHandler(config_manager)
        elif len(args) == 1:
            self.config_manager = args[0]
            # Establecer valores por defecto para compatibilidad
            self.camera_ip = getattr(self.config_manager, 'ip', 'unknown')
            self.credentials = {}
            self.config = self.config_manager if hasattr(self.config_manager, 'ip') else None
            self.streaming_config = StreamingConfig()
        else:
            raise ValueError("Argumentos de inicialización inválidos")
    
    # ==========================================
    # PROPIEDADES (Nueva Arquitectura)
    # ==========================================
    
    @property
    def state(self) -> ConnectionState:
        """Estado actual de la conexión."""
        return self._state
    
    @property
    def is_connected(self) -> bool:
        """
        Indica si está conectado.
        Mantiene compatibilidad con API antigua.
        """
        return self._state in [ConnectionState.CONNECTED, ConnectionState.STREAMING]
    
    @property
    def is_streaming(self) -> bool:
        """Indica si está haciendo streaming."""
        return self._state == ConnectionState.STREAMING
    
    @property
    def current_fps(self) -> float:
        """FPS actual del streaming."""
        return self._fps
    
    # ==========================================
    # MÉTODOS ABSTRACTOS (Interfaz Principal)
    # ==========================================
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establece conexión con la cámara (async).
        
        Returns:
            True si la conexión fue exitosa
            
        Raises:
            ConnectionError: Si no se puede establecer la conexión
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Cierra la conexión con la cámara (async).
        
        Returns:
            True si se desconectó correctamente
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Prueba la conexión sin establecerla permanentemente.
        
        Returns:
            True si la conexión es posible
        """
        pass
    
    @abstractmethod
    async def capture_snapshot(self) -> Optional[bytes]:
        """
        Captura un snapshot de la cámara.
        
        Returns:
            Datos de imagen en bytes o None si falla
        """
        pass
    
    @abstractmethod
    async def start_streaming(self) -> bool:
        """
        Inicia el streaming de video.
        
        Returns:
            True si el streaming se inició exitosamente
        """
        pass
    
    @abstractmethod
    async def stop_streaming(self) -> bool:
        """
        Detiene el streaming de video.
        
        Returns:
            True si el streaming se detuvo exitosamente
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> ProtocolCapabilities:
        """
        Obtiene las capacidades del protocolo.
        
        Returns:
            Capacidades del protocolo
        """
        pass
    
    # ==========================================
    # MÉTODOS DE COMPATIBILIDAD (API Antigua)
    # ==========================================
    
    def is_alive(self) -> bool:
        """
        Verifica si la conexión está activa (compatibilidad).
        
        Returns:
            True si la conexión está activa
        """
        return self.is_connected
    
    def get_frame(self) -> Optional[Any]:
        """
        Obtiene un frame/imagen de la cámara (compatibilidad síncrona).
        
        Returns:
            Frame de video o imagen, None si no se puede obtener
        """
        # Implementación por defecto para compatibilidad
        # Los handlers específicos pueden sobrescribir
        if self._stream_handle and self.is_streaming:
            ret, frame = self._stream_handle.read()
            return frame if ret else None
        return None
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre el estado de la conexión.
        
        Returns:
            Diccionario con información de la conexión
        """
        return {
            "camera_ip": getattr(self, 'camera_ip', 'unknown'),
            "is_connected": self.is_connected,
            "connection_type": self.__class__.__name__,
            "username": getattr(self, 'credentials', {}).get('username', ''),
            "state": self._state.value,
            "fps": self._fps,
            "frame_count": self._frame_count,
            "last_frame": self._last_frame_time.isoformat() if self._last_frame_time else None
        }
    
    def validate_credentials(self) -> bool:
        """
        Valida que las credenciales estén completas.
        
        Returns:
            True si las credenciales son válidas
        """
        if hasattr(self, 'credentials') and self.credentials:
            required_fields = ["username", "password"]
            return all(field in self.credentials and self.credentials[field] 
                      for field in required_fields)
        
        # Para nueva API, usar config
        if hasattr(self, 'config') and self.config:
            return bool(self.config.username)
        
        return True  # Permitir conexiones sin autenticación
    
    # ==========================================
    # CONTEXT MANAGER SUPPORT
    # ==========================================
    
    def __enter__(self):
        """
        Soporte para context manager - establece conexión.
        """
        # Para compatibilidad, intentar conexión síncrona
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if not loop.run_until_complete(self.connect()):
            raise ConnectionError(f"No se pudo conectar a la cámara {self.camera_ip}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Soporte para context manager - cierra conexión.
        """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.disconnect())
    
    # ==========================================
    # FRAME CALLBACKS (Nueva Funcionalidad)
    # ==========================================
    
    def add_frame_callback(self, callback: Callable[[Any], None]):
        """Agrega callback para frames recibidos."""
        self._frame_callbacks.append(callback)
    
    def remove_frame_callback(self, callback: Callable[[Any], None]):
        """Remueve callback de frames."""
        if callback in self._frame_callbacks:
            self._frame_callbacks.remove(callback)
    
    def _notify_frame_callbacks(self, frame: Any):
        """Notifica a todos los callbacks de frame."""
        for callback in self._frame_callbacks:
            try:
                callback(frame)
            except Exception as e:
                self.logger.error(f"Error en callback de frame: {str(e)}")
    
    # ==========================================
    # GESTIÓN DE ESTADO INTERNO
    # ==========================================
    
    def _set_state(self, new_state: ConnectionState):
        """Cambia el estado de la conexión."""
        old_state = self._state
        self._state = new_state
        if old_state != new_state:
            self.logger.info(f"Estado cambiado: {old_state.value} → {new_state.value}")
    
    def _update_frame_stats(self, frame: Any):
        """Actualiza estadísticas de frames."""
        current_time = time.time()
        
        if hasattr(self, '_frame_times'):
            self._frame_times.append(current_time)
            if len(self._frame_times) > 30:
                self._frame_times.pop(0)
        else:
            self._frame_times = [current_time]
        
        # Calcular FPS
        if len(self._frame_times) >= 2:
            time_diff = self._frame_times[-1] - self._frame_times[0]
            if time_diff > 0:
                self._fps = (len(self._frame_times) - 1) / time_diff
        
        self._frame_count += 1
        self._last_frame_time = datetime.now()
    
    # ==========================================
    # REPRESENTACIÓN STRING
    # ==========================================
    
    def __str__(self) -> str:
        """Representación en string del handler."""
        camera_ip = getattr(self, 'camera_ip', 'unknown')
        status = "conectado" if self.is_connected else "desconectado"
        return f"{self.__class__.__name__}({camera_ip}) - {status}"
    
    def __repr__(self) -> str:
        """Representación detallada del handler."""
        return (f"{self.__class__.__name__}("
                f"ip={getattr(self, 'camera_ip', 'unknown')}, "
                f"state={self._state.value}, "
                f"fps={self._fps:.1f})") 