"""
Modelos Pydantic para la API de cámaras.

Define los esquemas de request/response para la nueva estructura 3FN.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class ConnectionStatus(str, Enum):
    """Estados de conexión de una cámara."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    STREAMING = "streaming"
    UNAVAILABLE = "unavailable"


class ProtocolType(str, Enum):
    """Tipos de protocolo soportados."""

    RTSP = "rtsp"
    ONVIF = "onvif"
    HTTP = "http"
    HTTPS = "https"
    CGI = "cgi"
    AMCREST = "amcrest"
    GENERIC = "generic"


class AuthType(str, Enum):
    """Tipos de autenticación."""

    BASIC = "basic"
    DIGEST = "digest"
    BEARER = "bearer"
    CUSTOM = "custom"


# === Modelos de Request ===


class CredentialsRequest(BaseModel):
    """Credenciales para autenticación."""

    username: str = Field(..., min_length=1, description="Nombre de usuario")
    password: str = Field(..., min_length=1, description="Contraseña")
    auth_type: AuthType = Field(
        default=AuthType.BASIC, description="Tipo de autenticación"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "password123",
                "auth_type": "basic",
            }
        }


class ProtocolConfigRequest(BaseModel):
    """Configuración de protocolo."""

    protocol_type: ProtocolType = Field(..., description="Tipo de protocolo")
    port: int = Field(..., ge=1, le=65535, description="Puerto del protocolo")
    is_enabled: bool = Field(default=True, description="Si está habilitado")
    is_primary: bool = Field(default=False, description="Si es el protocolo principal")
    version: Optional[str] = Field(None, description="Versión del protocolo")

    class Config:
        json_schema_extra = {
            "example": {
                "protocol_type": "onvif",
                "port": 80,
                "is_enabled": True,
                "is_primary": True,
                "version": "2.0",
            }
        }


class EndpointRequest(BaseModel):
    """Endpoint/URL descubierto o configurado."""

    type: str = Field(..., description="Tipo de endpoint (rtsp_main, snapshot, etc)")
    url: str = Field(..., description="URL completa")
    protocol: Optional[ProtocolType] = Field(None, description="Protocolo usado")
    verified: bool = Field(default=False, description="Si fue verificada exitosamente")
    priority: int = Field(default=0, ge=0, description="Prioridad (0=mayor)")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "rtsp_main",
                "url": "rtsp://192.168.1.50:554/cam/realmonitor?channel=1&subtype=0",
                "protocol": "rtsp",
                "verified": True,
                "priority": 0,
            }
        }


class StreamProfileRequest(BaseModel):
    """Perfil de streaming."""

    profile_name: str = Field(..., description="Nombre del perfil")
    stream_type: str = Field(default="main", description="Tipo de stream (main/sub)")
    resolution: Optional[str] = Field(None, description="Resolución (1920x1080)")
    fps: Optional[int] = Field(None, ge=1, le=60, description="FPS")
    bitrate: Optional[int] = Field(None, ge=1, description="Bitrate en kbps")
    codec: Optional[str] = Field(None, description="Codec (H264/H265)")
    quality: Optional[str] = Field(None, description="Calidad (high/medium/low)")
    channel: int = Field(default=1, ge=1, description="Canal")
    subtype: int = Field(default=0, ge=0, description="Subtipo")
    is_default: bool = Field(default=False, description="Si es el perfil por defecto")


class CreateCameraRequest(BaseModel):
    """Request para crear una nueva cámara."""

    brand: str = Field(..., min_length=1, description="Marca de la cámara")
    model: str = Field(default="Unknown", description="Modelo de la cámara")
    display_name: str = Field(..., min_length=1, description="Nombre para mostrar")
    ip: str = Field(..., description="Dirección IP")
    location: Optional[str] = Field(None, description="Ubicación física")
    description: Optional[str] = Field(None, description="Descripción")

    # Credenciales
    credentials: CredentialsRequest

    # Protocolos opcionales
    protocols: Optional[List[ProtocolConfigRequest]] = Field(
        default=None, description="Configuración de protocolos"
    )

    # Endpoints opcionales
    endpoints: Optional[List[EndpointRequest]] = Field(
        default=None, description="URLs conocidas"
    )

    # Perfiles de streaming opcionales
    stream_profiles: Optional[List[StreamProfileRequest]] = Field(
        default=None, description="Perfiles de streaming"
    )

    @validator("ip")
    def validate_ip(cls, v):
        """Valida formato de IP."""
        import ipaddress

        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError("Dirección IP inválida")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "brand": "dahua",
                "model": "DH-IPC-HFW2431S",
                "display_name": "Cámara Principal",
                "ip": "192.168.1.50",
                "location": "Entrada principal",
                "description": "Cámara de seguridad entrada",
                "credentials": {"username": "admin", "password": "password123"},
                "protocols": [
                    {"protocol_type": "onvif", "port": 80, "is_primary": True},
                    {"protocol_type": "rtsp", "port": 554},
                ],
            }
        }


class UpdateCameraRequest(BaseModel):
    """Request para actualizar una cámara."""

    display_name: Optional[str] = Field(None, min_length=1)
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    # Credenciales opcionales
    credentials: Optional[CredentialsRequest] = None

    # Endpoints para agregar/actualizar
    endpoints: Optional[List[EndpointRequest]] = None

    # Perfiles de streaming
    stream_profiles: Optional[List[StreamProfileRequest]] = None


class TestConnectionRequest(BaseModel):
    """Request para probar conexión sin guardar."""

    ip: str = Field(..., description="Dirección IP")
    username: str = Field(..., description="Usuario")
    password: str = Field(..., description="Contraseña")
    protocol: ProtocolType = Field(default=ProtocolType.ONVIF)
    port: Optional[int] = Field(None, description="Puerto")
    brand: Optional[str] = Field(default="Generic")


# === Modelos para Gestión de Credenciales ===


class CreateCredentialRequest(BaseModel):
    """Request para crear una nueva credencial."""

    credential_name: str = Field(..., min_length=1, description="Nombre descriptivo")
    username: str = Field(..., min_length=1, description="Nombre de usuario")
    password: str = Field(..., min_length=1, description="Contraseña")
    auth_type: AuthType = Field(default=AuthType.BASIC, description="Tipo de autenticación")
    is_default: bool = Field(default=False, description="Si es la credencial por defecto")

    class Config:
        json_schema_extra = {
            "example": {
                "credential_name": "Admin Principal",
                "username": "admin",
                "password": "secure_password",
                "auth_type": "digest",
                "is_default": True
            }
        }


class UpdateCredentialRequest(BaseModel):
    """Request para actualizar una credencial existente."""

    credential_name: Optional[str] = Field(None, min_length=1)
    username: Optional[str] = Field(None, min_length=1)
    password: Optional[str] = Field(None, min_length=1, description="Dejar vacío para no cambiar")
    auth_type: Optional[AuthType] = None
    is_default: Optional[bool] = None


class CredentialDetailResponse(BaseModel):
    """Respuesta detallada de una credencial."""

    credential_id: int
    credential_name: str
    username: str
    auth_type: AuthType
    is_active: bool
    is_default: bool
    last_used: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "credential_id": 1,
                "credential_name": "Admin Principal",
                "username": "admin",
                "auth_type": "digest",
                "is_active": True,
                "is_default": True,
                "last_used": "2025-01-16T10:30:00",
                "created_at": "2025-01-01T08:00:00",
                "updated_at": "2025-01-15T14:20:00"
            }
        }


class CredentialListResponse(BaseModel):
    """Respuesta de lista de credenciales."""

    total: int
    credentials: List[CredentialDetailResponse]


# === Modelos para Gestión de Stream Profiles ===


class StreamType(str, Enum):
    """Tipos de stream soportados."""
    
    MAIN = "main"      # Stream principal (alta calidad)
    SUB = "sub"        # Stream secundario (calidad media)
    THIRD = "third"    # Stream terciario (baja calidad)
    MOBILE = "mobile"  # Stream optimizado para móvil


class VideoCodec(str, Enum):
    """Codecs de video soportados."""
    
    H264 = "H264"
    H265 = "H265"
    MJPEG = "MJPEG"
    MPEG4 = "MPEG4"


class StreamQuality(str, Enum):
    """Niveles de calidad predefinidos."""
    
    HIGHEST = "highest"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    LOWEST = "lowest"


class CreateStreamProfileRequest(BaseModel):
    """Request para crear un nuevo perfil de streaming."""
    
    profile_name: str = Field(..., min_length=1, max_length=50, description="Nombre único del perfil")
    stream_type: StreamType = Field(default=StreamType.MAIN, description="Tipo de stream")
    resolution: str = Field(..., pattern=r"^\d{3,4}x\d{3,4}$", description="Resolución (ej: 1920x1080)")
    fps: int = Field(..., ge=1, le=120, description="Frames por segundo")
    bitrate: int = Field(..., ge=64, le=50000, description="Bitrate en kbps")
    codec: VideoCodec = Field(default=VideoCodec.H264, description="Codec de video")
    quality: StreamQuality = Field(default=StreamQuality.HIGH, description="Nivel de calidad")
    gop_interval: Optional[int] = Field(None, ge=1, le=300, description="Intervalo GOP (Group of Pictures)")
    channel: int = Field(default=1, ge=1, le=16, description="Canal de la cámara")
    subtype: int = Field(default=0, ge=0, le=2, description="Subtipo del stream")
    is_default: bool = Field(default=False, description="Si es el perfil por defecto")
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_name": "HD Principal",
                "stream_type": "main",
                "resolution": "1920x1080",
                "fps": 30,
                "bitrate": 4096,
                "codec": "H264",
                "quality": "high",
                "gop_interval": 50,
                "channel": 1,
                "subtype": 0,
                "is_default": True
            }
        }


class UpdateStreamProfileRequest(BaseModel):
    """Request para actualizar un perfil de streaming."""
    
    profile_name: Optional[str] = Field(None, min_length=1, max_length=50)
    resolution: Optional[str] = Field(None, pattern=r"^\d{3,4}x\d{3,4}$")
    fps: Optional[int] = Field(None, ge=1, le=120)
    bitrate: Optional[int] = Field(None, ge=64, le=50000)
    codec: Optional[VideoCodec] = None
    quality: Optional[StreamQuality] = None
    gop_interval: Optional[int] = Field(None, ge=1, le=300)
    is_default: Optional[bool] = None


class StreamProfileDetailResponse(BaseModel):
    """Respuesta detallada de un perfil de streaming."""
    
    profile_id: int
    profile_name: str
    profile_token: Optional[str] = Field(None, description="Token ONVIF si aplica")
    stream_type: StreamType
    encoding: VideoCodec = Field(..., description="Codec de video")
    resolution: str
    framerate: int = Field(..., description="FPS configurado")
    bitrate: int = Field(..., description="Bitrate en kbps")
    quality: StreamQuality
    gop_interval: Optional[int] = None
    channel: int
    subtype: int
    is_default: bool
    is_active: bool
    endpoint_id: Optional[int] = Field(None, description="ID del endpoint asociado")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": 1,
                "profile_name": "HD Principal",
                "profile_token": "Profile_1",
                "stream_type": "main",
                "encoding": "H264",
                "resolution": "1920x1080",
                "framerate": 30,
                "bitrate": 4096,
                "quality": "high",
                "gop_interval": 50,
                "channel": 1,
                "subtype": 0,
                "is_default": True,
                "is_active": True,
                "endpoint_id": 5,
                "created_at": "2025-01-17T10:00:00",
                "updated_at": "2025-01-17T10:00:00"
            }
        }


class StreamProfileListResponse(BaseModel):
    """Respuesta de lista de perfiles de streaming."""
    
    total: int
    profiles: List[StreamProfileDetailResponse]


# === Modelos para Gestión de Protocolos ===


class ProtocolStatus(str, Enum):
    """Estado de un protocolo."""
    
    UNKNOWN = "unknown"
    TESTING = "testing"
    ACTIVE = "active"
    FAILED = "failed"
    DISABLED = "disabled"


class UpdateProtocolRequest(BaseModel):
    """Request para actualizar configuración de protocolo."""
    
    port: Optional[int] = Field(None, ge=1, le=65535, description="Puerto del protocolo")
    is_enabled: Optional[bool] = Field(None, description="Si está habilitado")
    is_primary: Optional[bool] = Field(None, description="Si es el protocolo principal")
    version: Optional[str] = Field(None, max_length=20, description="Versión del protocolo")
    path: Optional[str] = Field(None, max_length=255, description="Path específico del protocolo")
    
    class Config:
        json_schema_extra = {
            "example": {
                "port": 8080,
                "is_enabled": True,
                "is_primary": True,
                "version": "2.0"
            }
        }


class TestProtocolRequest(BaseModel):
    """Request para probar un protocolo específico."""
    
    timeout: int = Field(default=10, ge=1, le=60, description="Timeout en segundos")
    credential_id: Optional[int] = Field(None, description="ID de credencial específica a usar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timeout": 10,
                "credential_id": 1
            }
        }


class DiscoverProtocolsRequest(BaseModel):
    """Request para auto-descubrir protocolos."""
    
    scan_common_ports: bool = Field(default=True, description="Escanear puertos comunes")
    deep_scan: bool = Field(default=False, description="Escaneo profundo (más lento)")
    timeout: int = Field(default=30, ge=5, le=300, description="Timeout total en segundos")
    credential_ids: Optional[List[int]] = Field(None, description="IDs de credenciales a probar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "scan_common_ports": True,
                "deep_scan": False,
                "timeout": 30,
                "credential_ids": [1, 2]
            }
        }


class ProtocolDetailResponse(BaseModel):
    """Respuesta detallada de un protocolo."""
    
    protocol_id: int
    protocol_type: ProtocolType
    port: int
    is_enabled: bool
    is_primary: bool
    is_verified: bool
    status: ProtocolStatus
    version: Optional[str] = None
    path: Optional[str] = None
    last_tested: Optional[datetime] = None
    last_error: Optional[str] = None
    response_time_ms: Optional[int] = None
    capabilities: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "protocol_id": 1,
                "protocol_type": "onvif",
                "port": 80,
                "is_enabled": True,
                "is_primary": True,
                "is_verified": True,
                "status": "active",
                "version": "2.0",
                "path": "/onvif/device_service",
                "last_tested": "2025-01-17T10:00:00",
                "response_time_ms": 150,
                "capabilities": {
                    "ptz": True,
                    "analytics": False,
                    "events": True
                },
                "created_at": "2025-01-01T08:00:00",
                "updated_at": "2025-01-17T10:00:00"
            }
        }


class ProtocolListResponse(BaseModel):
    """Respuesta de lista de protocolos."""
    
    total: int
    protocols: List[ProtocolDetailResponse]


class TestProtocolResponse(BaseModel):
    """Respuesta de prueba de protocolo."""
    
    success: bool
    protocol_type: ProtocolType
    port: int
    response_time_ms: Optional[int] = None
    version_detected: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "protocol_type": "onvif",
                "port": 80,
                "response_time_ms": 150,
                "version_detected": "2.0",
                "capabilities": {
                    "profiles": ["Profile_1", "Profile_2"],
                    "ptz": True,
                    "analytics": False
                },
                "message": "Protocolo ONVIF verificado exitosamente"
            }
        }


class DiscoverProtocolsResponse(BaseModel):
    """Respuesta de auto-discovery de protocolos."""
    
    discovered_count: int
    scan_duration_ms: int
    protocols_found: List[Dict[str, Any]]
    ports_scanned: List[int]
    credentials_tested: int
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "discovered_count": 3,
                "scan_duration_ms": 5420,
                "protocols_found": [
                    {
                        "protocol_type": "onvif",
                        "port": 80,
                        "version": "2.0",
                        "verified": True
                    },
                    {
                        "protocol_type": "rtsp",
                        "port": 554,
                        "verified": True
                    }
                ],
                "ports_scanned": [80, 81, 554, 8080, 8000],
                "credentials_tested": 2,
                "message": "Discovery completado. Encontrados 3 protocolos activos."
            }
        }


# === Modelos para Endpoints de Solo Lectura ===


class EventType(str, Enum):
    """Tipos de eventos del sistema."""
    
    CONNECTION = "connection"
    DISCONNECTION = "disconnection"
    ERROR = "error"
    CONFIG_CHANGE = "config_change"
    DISCOVERY = "discovery"
    SNAPSHOT = "snapshot"
    STREAM_START = "stream_start"
    STREAM_STOP = "stream_stop"
    AUTH_FAILURE = "auth_failure"


class EventSeverity(str, Enum):
    """Severidad de eventos."""
    
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class CameraEventResponse(BaseModel):
    """Respuesta de evento de cámara."""
    
    event_id: int
    event_type: EventType
    severity: EventSeverity
    timestamp: datetime
    message: str
    details: Optional[Dict[str, Any]] = None
    user: Optional[str] = None
    ip_address: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": 1234,
                "event_type": "connection",
                "severity": "info",
                "timestamp": "2025-01-17T10:30:00",
                "message": "Conexión establecida exitosamente",
                "details": {
                    "protocol": "onvif",
                    "port": 80,
                    "response_time_ms": 150
                }
            }
        }


class CameraEventsResponse(BaseModel):
    """Respuesta paginada de eventos."""
    
    total: int
    page: int
    page_size: int
    events: List[CameraEventResponse]


class LogEntry(BaseModel):
    """Entrada de log de cámara."""
    
    log_id: int
    timestamp: datetime
    level: str  # DEBUG, INFO, WARNING, ERROR
    component: str  # connection, streaming, discovery, etc
    message: str
    context: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "log_id": 5678,
                "timestamp": "2025-01-17T10:30:45",
                "level": "INFO",
                "component": "connection",
                "message": "RTSP stream connected successfully",
                "context": {
                    "url": "rtsp://192.168.1.50:554/stream",
                    "profile": "main"
                },
                "duration_ms": 250
            }
        }


class CameraLogsResponse(BaseModel):
    """Respuesta paginada de logs."""
    
    total: int
    page: int
    page_size: int
    logs: List[LogEntry]


class SnapshotInfo(BaseModel):
    """Información de snapshot/captura."""
    
    snapshot_id: int
    filename: str
    timestamp: datetime
    file_size: int  # en bytes
    width: int
    height: int
    format: str  # jpeg, png, etc
    stream_profile: Optional[str] = None
    trigger: str  # manual, scheduled, motion, etc
    storage_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "snapshot_id": 789,
                "filename": "camera1_20250117_103045.jpg",
                "timestamp": "2025-01-17T10:30:45",
                "file_size": 245678,
                "width": 1920,
                "height": 1080,
                "format": "jpeg",
                "stream_profile": "main",
                "trigger": "manual"
            }
        }


class CameraSnapshotsResponse(BaseModel):
    """Respuesta paginada de snapshots."""
    
    total: int
    page: int
    page_size: int
    snapshots: List[SnapshotInfo]


class CapabilityCategory(str, Enum):
    """Categorías de capacidades."""
    
    VIDEO = "video"
    AUDIO = "audio"
    PTZ = "ptz"
    ANALYTICS = "analytics"
    EVENTS = "events"
    NETWORK = "network"
    STORAGE = "storage"


class CapabilityDetail(BaseModel):
    """Detalle de una capacidad específica."""
    
    name: str
    supported: bool
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "motion_detection",
                "supported": True,
                "details": {
                    "zones": 4,
                    "sensitivity_levels": 10,
                    "algorithms": ["basic", "advanced"]
                }
            }
        }


class CameraCapabilitiesDetailResponse(BaseModel):
    """Respuesta detallada de capacidades de cámara."""
    
    camera_id: str
    last_updated: datetime
    discovery_method: str  # auto, manual, onvif
    categories: Dict[CapabilityCategory, List[CapabilityDetail]]
    raw_capabilities: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "123e4567-e89b-12d3-a456-426614174000",
                "last_updated": "2025-01-17T10:00:00",
                "discovery_method": "onvif",
                "categories": {
                    "video": [
                        {
                            "name": "h264_encoding",
                            "supported": True,
                            "details": {"profiles": ["baseline", "main", "high"]}
                        },
                        {
                            "name": "h265_encoding",
                            "supported": True,
                            "details": {"profiles": ["main"]}
                        }
                    ],
                    "ptz": [
                        {
                            "name": "pan_tilt",
                            "supported": False
                        }
                    ]
                }
            }
        }


# === Modelos de Response ===


class CredentialsResponse(BaseModel):
    """Respuesta de credenciales (sin contraseña)."""

    username: str
    auth_type: AuthType
    is_configured: bool = Field(..., description="Si tiene contraseña configurada")


class ProtocolResponse(BaseModel):
    """Respuesta de configuración de protocolo."""

    protocol_id: Optional[int] = None
    protocol_type: ProtocolType
    port: int
    is_enabled: bool
    is_primary: bool
    version: Optional[str] = None


class EndpointResponse(BaseModel):
    """Respuesta de endpoint."""

    endpoint_id: Optional[int] = None
    type: str
    url: str
    protocol: Optional[ProtocolType] = None
    is_verified: bool
    last_verified: Optional[datetime] = None
    response_time_ms: Optional[int] = None
    priority: int


class StreamProfileResponse(BaseModel):
    """Respuesta de perfil de streaming."""

    profile_id: Optional[int] = None
    profile_name: str
    stream_type: str
    resolution: Optional[str] = None
    fps: Optional[int] = None
    bitrate: Optional[int] = None
    codec: Optional[str] = None
    quality: Optional[str] = None
    channel: int
    subtype: int
    is_default: bool


class CameraStatisticsResponse(BaseModel):
    """Estadísticas de una cámara."""

    total_connections: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    success_rate: float = 0.0
    total_uptime_minutes: int = 0
    average_fps: Optional[float] = None
    average_latency_ms: Optional[int] = None
    last_connection_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    last_error_message: Optional[str] = None


class CameraCapabilitiesResponse(BaseModel):
    """Capacidades de la cámara."""

    supported_protocols: List[ProtocolType] = []
    has_ptz: bool = False
    has_audio: bool = False
    has_ir: bool = False
    has_motion_detection: bool = False
    max_resolution: Optional[str] = None
    supported_codecs: List[str] = []


class CameraResponse(BaseModel):
    """Respuesta completa de una cámara."""

    # Identificación
    camera_id: str
    brand: str
    model: str
    display_name: str

    # Conexión
    ip_address: str
    mac_address: Optional[str] = None

    # Estado
    status: ConnectionStatus
    is_active: bool
    is_connected: bool
    is_streaming: bool

    # Hardware info
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    serial_number: Optional[str] = None

    # Ubicación
    location: Optional[str] = None
    description: Optional[str] = None

    # Configuración
    credentials: Optional[CredentialsResponse] = None
    protocols: List[ProtocolResponse] = []
    endpoints: List[EndpointResponse] = []
    stream_profiles: List[StreamProfileResponse] = []

    # Capacidades
    capabilities: CameraCapabilitiesResponse

    # Estadísticas
    statistics: Optional[CameraStatisticsResponse] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "dahua_dh-ipc-hfw2431s_192168150",
                "brand": "dahua",
                "model": "DH-IPC-HFW2431S",
                "display_name": "Cámara Principal",
                "ip_address": "192.168.1.50",
                "status": "connected",
                "is_active": True,
                "is_connected": True,
                "is_streaming": False,
                "location": "Entrada principal",
                "credentials": {
                    "username": "admin",
                    "auth_type": "basic",
                    "is_configured": True,
                },
                "protocols": [
                    {
                        "protocol_type": "onvif",
                        "port": 80,
                        "is_enabled": True,
                        "is_primary": True,
                    }
                ],
                "endpoints": [
                    {
                        "type": "rtsp_main",
                        "url": "rtsp://192.168.1.50:554/cam/realmonitor?channel=1&subtype=0",
                        "is_verified": True,
                        "priority": 0,
                    }
                ],
                "capabilities": {
                    "supported_protocols": ["onvif", "rtsp"],
                    "has_ptz": False,
                    "has_audio": True,
                },
                "created_at": "2025-07-15T10:00:00Z",
                "updated_at": "2025-07-15T10:00:00Z",
            }
        }


class CameraListResponse(BaseModel):
    """Respuesta para listado de cámaras."""

    total: int = Field(..., description="Total de cámaras")
    cameras: List[CameraResponse] = Field(..., description="Lista de cámaras")


class TestConnectionResponse(BaseModel):
    """Respuesta de prueba de conexión."""

    success: bool
    message: str
    discovered_endpoints: Optional[List[EndpointResponse]] = None
    detected_capabilities: Optional[CameraCapabilitiesResponse] = None
