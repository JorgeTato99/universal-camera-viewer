"""
Schemas para mensajes WebSocket.

Define la estructura de mensajes para comunicación en tiempo real.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


# === Enums ===

class WSMessageType(str, Enum):
    """Tipos de mensajes WebSocket."""
    # Control
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    
    # Streaming
    START_STREAM = "start_stream"
    STOP_STREAM = "stop_stream"
    PAUSE_STREAM = "pause_stream"
    RESUME_STREAM = "resume_stream"
    FRAME = "frame"
    STREAM_STATUS = "stream_status"
    
    # Eventos
    EVENT = "event"
    NOTIFICATION = "notification"
    ALERT = "alert"
    
    # Control de cámara
    PTZ_COMMAND = "ptz_command"
    CAMERA_CONTROL = "camera_control"


class StreamFormat(str, Enum):
    """Formatos de stream soportados."""
    JPEG = "jpeg"
    H264 = "h264"
    H265 = "h265"
    MJPEG = "mjpeg"


class PTZAction(str, Enum):
    """Acciones PTZ."""
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    HOME = "home"
    PRESET = "preset"


class EventType(str, Enum):
    """Tipos de eventos del sistema."""
    CAMERA_CONNECTED = "camera_connected"
    CAMERA_DISCONNECTED = "camera_disconnected"
    MOTION_DETECTED = "motion_detected"
    CONNECTION_LOST = "connection_lost"
    CONNECTION_RESTORED = "connection_restored"
    RECORDING_STARTED = "recording_started"
    RECORDING_STOPPED = "recording_stopped"
    ERROR_OCCURRED = "error_occurred"
    
    # Eventos de publicación remota
    REMOTE_PUBLICATION_STARTED = "remote_publication_started"
    REMOTE_PUBLICATION_STOPPED = "remote_publication_stopped"
    REMOTE_PUBLICATION_ERROR = "remote_publication_error"
    REMOTE_SERVER_CONNECTED = "remote_server_connected"
    REMOTE_SERVER_DISCONNECTED = "remote_server_disconnected"


# === Mensajes Cliente → Servidor ===

class WSClientMessage(BaseModel):
    """Mensaje base del cliente."""
    
    action: WSMessageType = Field(..., description="Tipo de acción")
    params: Optional[Dict[str, Any]] = Field(None, description="Parámetros de la acción")
    request_id: Optional[str] = Field(None, description="ID único del request")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "start_stream",
                "params": {
                    "quality": "high",
                    "fps": 30
                },
                "request_id": "req_123"
            }
        }


class StartStreamRequest(BaseModel):
    """Parámetros para iniciar stream."""
    
    quality: str = Field("medium", description="Calidad del stream")
    fps: Optional[int] = Field(None, ge=1, le=60, description="FPS objetivo")
    format: StreamFormat = Field(StreamFormat.JPEG, description="Formato del stream")
    resolution: Optional[str] = Field(None, description="Resolución (ej: 1280x720)")
    audio: bool = Field(False, description="Incluir audio")
    
    @validator('resolution')
    def validate_resolution(cls, v):
        """Valida formato de resolución."""
        if v is not None:
            if 'x' not in v:
                raise ValueError("Resolución debe tener formato WIDTHxHEIGHT")
            parts = v.lower().split('x')
            if len(parts) != 2 or not all(p.isdigit() for p in parts):
                raise ValueError("Resolución inválida")
        return v


class PTZCommandRequest(BaseModel):
    """Comando PTZ."""
    
    action: PTZAction = Field(..., description="Acción PTZ")
    speed: float = Field(1.0, ge=0.1, le=1.0, description="Velocidad del movimiento")
    duration: Optional[float] = Field(None, ge=0.1, le=10.0, description="Duración en segundos")
    preset_number: Optional[int] = Field(None, ge=1, le=255, description="Número de preset")
    
    @validator('preset_number')
    def validate_preset(cls, v, values):
        """Valida que preset_number solo se use con action PRESET."""
        if v is not None and values.get('action') != PTZAction.PRESET:
            raise ValueError("preset_number solo se usa con action=preset")
        return v


# === Mensajes Servidor → Cliente ===

class WSServerMessage(BaseModel):
    """Mensaje base del servidor."""
    
    type: WSMessageType = Field(..., description="Tipo de mensaje")
    data: Optional[Dict[str, Any]] = Field(None, description="Datos del mensaje")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="ID del request relacionado")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "frame",
                "data": {
                    "camera_id": "cam_123",
                    "frame_data": "base64..."
                },
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }


class FrameMessage(BaseModel):
    """Mensaje de frame de video."""
    
    camera_id: str = Field(..., description="ID de la cámara")
    data: str = Field(..., description="Datos del frame en base64")
    frame_number: int = Field(..., ge=0, description="Número de frame")
    timestamp: datetime = Field(..., description="Timestamp del frame")
    format: StreamFormat = Field(..., description="Formato del frame")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Métricas del frame")
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "cam_123",
                "data": "base64_encoded_jpeg_data",
                "frame_number": 1234,
                "timestamp": "2024-01-15T10:00:00.123Z",
                "format": "jpeg",
                "metrics": {
                    "fps": 29.5,
                    "bitrate_kbps": 2500,
                    "quality": "high"
                }
            }
        }


class StreamStatusMessage(BaseModel):
    """Estado del stream."""
    
    camera_id: str = Field(..., description="ID de la cámara")
    is_active: bool = Field(..., description="Si el stream está activo")
    quality: str = Field(..., description="Calidad actual")
    fps: float = Field(..., description="FPS actual")
    bitrate_kbps: Optional[float] = Field(None, description="Bitrate en kbps")
    resolution: str = Field(..., description="Resolución actual")
    clients_connected: int = Field(..., description="Clientes conectados")
    duration_seconds: float = Field(..., description="Duración del stream")
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "cam_123",
                "is_active": True,
                "quality": "high",
                "fps": 29.97,
                "bitrate_kbps": 4000,
                "resolution": "1920x1080",
                "clients_connected": 3,
                "duration_seconds": 120.5
            }
        }


class EventMessage(BaseModel):
    """Mensaje de evento del sistema."""
    
    event_type: EventType = Field(..., description="Tipo de evento")
    source: str = Field(..., description="Origen del evento")
    severity: str = Field("info", description="Severidad: debug, info, warning, error, critical")
    title: str = Field(..., description="Título del evento")
    description: Optional[str] = Field(None, description="Descripción detallada")
    data: Optional[Dict[str, Any]] = Field(None, description="Datos adicionales")
    
    @validator('severity')
    def validate_severity(cls, v):
        """Valida nivel de severidad."""
        valid_levels = ['debug', 'info', 'warning', 'error', 'critical']
        if v not in valid_levels:
            raise ValueError(f"Severidad debe ser una de: {', '.join(valid_levels)}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "motion_detected",
                "source": "cam_123",
                "severity": "warning",
                "title": "Movimiento detectado",
                "description": "Se detectó movimiento en la entrada principal",
                "data": {
                    "confidence": 0.85,
                    "area": "entrance",
                    "timestamp": "2024-01-15T10:00:00Z"
                }
            }
        }


class ErrorMessage(BaseModel):
    """Mensaje de error."""
    
    error_code: str = Field(..., description="Código de error")
    message: str = Field(..., description="Mensaje de error")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales")
    recoverable: bool = Field(True, description="Si el error es recuperable")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "STREAM_FAILED",
                "message": "No se pudo conectar con la cámara",
                "details": {
                    "camera_id": "cam_123",
                    "reason": "timeout"
                },
                "recoverable": True
            }
        }


# === Validadores de mensajes ===

def validate_ws_message(message: Dict[str, Any]) -> Optional[WSClientMessage]:
    """
    Valida un mensaje WebSocket del cliente.
    
    Args:
        message: Diccionario con el mensaje
        
    Returns:
        Mensaje validado o None si es inválido
    """
    try:
        return WSClientMessage(**message)
    except Exception as e:
        logger.warning(f"Mensaje WebSocket inválido: {e}")
        return None


def create_frame_message(
    camera_id: str,
    frame_data: bytes,
    frame_number: int,
    format: StreamFormat = StreamFormat.JPEG,
    metrics: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Crea un mensaje de frame para enviar.
    
    Args:
        camera_id: ID de la cámara
        frame_data: Datos del frame
        frame_number: Número de frame
        format: Formato del frame
        metrics: Métricas opcionales
        
    Returns:
        Diccionario con el mensaje
    """
    import base64
    
    frame_msg = FrameMessage(
        camera_id=camera_id,
        data=base64.b64encode(frame_data).decode('utf-8'),
        frame_number=frame_number,
        timestamp=datetime.utcnow(),
        format=format,
        metrics=metrics
    )
    
    return WSServerMessage(
        type=WSMessageType.FRAME,
        data=frame_msg.dict()
    ).dict()


def create_event_message(
    event_type: EventType,
    source: str,
    title: str,
    severity: str = "info",
    description: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Crea un mensaje de evento.
    
    Args:
        event_type: Tipo de evento
        source: Origen del evento
        title: Título del evento
        severity: Severidad
        description: Descripción opcional
        data: Datos adicionales
        
    Returns:
        Diccionario con el mensaje
    """
    event_msg = EventMessage(
        event_type=event_type,
        source=source,
        severity=severity,
        title=title,
        description=description,
        data=data
    )
    
    return WSServerMessage(
        type=WSMessageType.EVENT,
        data=event_msg.dict()
    ).dict()


def create_error_message(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    recoverable: bool = True,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crea un mensaje de error.
    
    Args:
        error_code: Código de error
        message: Mensaje de error
        details: Detalles adicionales
        recoverable: Si es recuperable
        request_id: ID del request relacionado
        
    Returns:
        Diccionario con el mensaje
    """
    error_msg = ErrorMessage(
        error_code=error_code,
        message=message,
        details=details,
        recoverable=recoverable
    )
    
    return WSServerMessage(
        type=WSMessageType.ERROR,
        data=error_msg.dict(),
        request_id=request_id
    ).dict()


# Import logger si es necesario
import logging
logger = logging.getLogger(__name__)