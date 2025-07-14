"""
Modelo de dominio para streams de video.

Define el estado y configuración de un stream de video activo.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import uuid


class StreamStatus(Enum):
    """Estados posibles de un stream."""
    IDLE = "idle"
    CONNECTING = "connecting"
    STREAMING = "streaming"
    PAUSED = "paused"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class StreamProtocol(Enum):
    """Protocolos de streaming soportados."""
    RTSP = "rtsp"
    ONVIF = "onvif"
    HTTP = "http"
    GENERIC = "generic"


@dataclass
class StreamModel:
    """
    Modelo que representa un stream de video activo.
    
    Attributes:
        stream_id: Identificador único del stream
        camera_id: ID de la cámara asociada
        protocol: Protocolo utilizado para el streaming
        status: Estado actual del stream
        fps: Frames por segundo actuales
        target_fps: FPS objetivo configurado
        frame_count: Contador total de frames procesados
        dropped_frames: Contador de frames perdidos
        start_time: Timestamp de inicio del stream
        last_frame_time: Timestamp del último frame recibido
        error_message: Mensaje de error si status es ERROR
        metadata: Metadatos adicionales del stream
    """
    
    # Identificadores
    stream_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    camera_id: str = ""
    
    # Configuración
    protocol: StreamProtocol = StreamProtocol.RTSP
    target_fps: int = 30
    buffer_size: int = 5
    
    # Estado
    status: StreamStatus = StreamStatus.IDLE
    fps: float = 0.0
    frame_count: int = 0
    dropped_frames: int = 0
    
    # Timestamps
    start_time: Optional[datetime] = None
    last_frame_time: Optional[datetime] = None
    
    # Error handling
    error_message: Optional[str] = None
    reconnect_attempts: int = 0
    
    # Metadatos
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validación después de inicialización."""
        self.validate()
    
    def validate(self) -> None:
        """Valida la integridad del modelo."""
        if not self.camera_id:
            raise ValueError("camera_id es obligatorio")
        
        if self.target_fps < 1 or self.target_fps > 60:
            raise ValueError(f"target_fps debe estar entre 1 y 60, recibido: {self.target_fps}")
        
        if self.buffer_size < 1 or self.buffer_size > 30:
            raise ValueError(f"buffer_size debe estar entre 1 y 30, recibido: {self.buffer_size}")
    
    def start(self) -> None:
        """Marca el stream como iniciado."""
        self.status = StreamStatus.CONNECTING
        self.start_time = datetime.now()
        self.frame_count = 0
        self.dropped_frames = 0
        self.error_message = None
    
    def update_frame(self) -> None:
        """Actualiza contadores cuando se recibe un frame."""
        self.frame_count += 1
        self.last_frame_time = datetime.now()
        
        if self.status != StreamStatus.STREAMING:
            self.status = StreamStatus.STREAMING
    
    def calculate_fps(self) -> float:
        """Calcula los FPS actuales basado en el tiempo transcurrido."""
        if not self.start_time or self.frame_count == 0:
            return 0.0
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if elapsed > 0:
            self.fps = self.frame_count / elapsed
            return self.fps
        
        return 0.0
    
    def mark_error(self, error_message: str) -> None:
        """Marca el stream con error."""
        self.status = StreamStatus.ERROR
        self.error_message = error_message
        self.reconnect_attempts += 1
    
    def stop(self) -> None:
        """Detiene el stream."""
        self.status = StreamStatus.DISCONNECTED
        self.fps = 0.0
    
    def is_active(self) -> bool:
        """Verifica si el stream está activo."""
        return self.status in [StreamStatus.CONNECTING, StreamStatus.STREAMING, StreamStatus.PAUSED]
    
    def get_uptime_seconds(self) -> float:
        """Obtiene el tiempo de actividad en segundos."""
        if not self.start_time:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario."""
        return {
            'stream_id': self.stream_id,
            'camera_id': self.camera_id,
            'protocol': self.protocol.value,
            'status': self.status.value,
            'fps': self.fps,
            'target_fps': self.target_fps,
            'frame_count': self.frame_count,
            'dropped_frames': self.dropped_frames,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'last_frame_time': self.last_frame_time.isoformat() if self.last_frame_time else None,
            'error_message': self.error_message,
            'reconnect_attempts': self.reconnect_attempts,
            'uptime_seconds': self.get_uptime_seconds(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamModel':
        """Crea una instancia desde un diccionario."""
        # Convertir strings a enums
        if 'protocol' in data and isinstance(data['protocol'], str):
            data['protocol'] = StreamProtocol(data['protocol'])
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = StreamStatus(data['status'])
        
        # Convertir timestamps
        if 'start_time' in data and data['start_time']:
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if 'last_frame_time' in data and data['last_frame_time']:
            data['last_frame_time'] = datetime.fromisoformat(data['last_frame_time'])
        
        # Remover campos calculados
        data.pop('uptime_seconds', None)
        
        return cls(**data)